import logging
from collections.abc import Generator, Iterable

from hermes.chat.events import EngineCommandEvent, Event, MessageEvent, RawContentForHistoryEvent, SaveHistoryEvent
from hermes.chat.file_operations_handler import FileOperationsHandler
from hermes.chat.history import History
from hermes.chat.interface.helpers.cli_notifications import CLIColors, CLINotificationsPrinter
from hermes.chat.messages import TextMessage
from hermes.chat.participants import DebugParticipant, LLMParticipant, Participant

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    def __init__(
        self,
        user_participant: Participant,
        assistant_participant: LLMParticipant | DebugParticipant,
        history: History,
    ):
        self.user_participant = user_participant
        self.assistant_participant = assistant_participant
        self.participants = [self.user_participant, self.assistant_participant]
        self.history = history
        self.notifications_printer = CLINotificationsPrinter()

        self.file_operations_handler = FileOperationsHandler(self.notifications_printer)
        self._received_assistant_done_event = False
        self._should_exit_after_one_cycle = False

    def start_conversation(self):
        try:
            self._start_conversation()
        except EOFError as e:
            raise e
        except Exception as e:
            self._handle_save_history(SaveHistoryEvent())
            raise e

    def _start_conversation(self):
        while self._should_continue_conversation():
            self._run_conversation_cycle_and_handle_exceptions()

    def _should_continue_conversation(self) -> bool:
        return not self._should_exit_after_one_cycle

    def _run_conversation_cycle_and_handle_exceptions(self):
        try:
            self._run_conversation_cycle()
        except KeyboardInterrupt:
            self._handle_interruption()
        except EOFError as e:
            raise e
        except Exception as e:
            import traceback
            self.notifications_printer.print_notification(f"Conversation cycle failed with {e}", CLIColors.RED)
            print(traceback.format_exc())
            self._handle_interruption()

    def _run_conversation_cycle(self):
        self._prepare_for_conversation_cycle()

        events_from_user = self._get_user_input_and_run_commands()
        self._consume_events_from_user_and_render_assistant(events_from_user)

        events_from_assistant = self._get_assistant_input_and_run_commands()
        self._consume_events_from_assistant_and_render_user(events_from_assistant)

        self._commit_history()

    def _prepare_for_conversation_cycle(self):
        self._received_assistant_done_event = False
        self._should_exit_after_one_cycle = False

    def _get_user_input_and_run_commands(self) -> list[Event]:
        return list(self.user_participant.get_input_and_run_commands())

    def _consume_events_from_user_and_render_assistant(self, events: list[Event]):
        events = list(self._swallow_engine_commands_from_stream(events))
        events = list(self._track_events_in_history(events))
        history_snapshot = self.history.get_history_for(self.assistant_participant.get_name())
        self.assistant_participant.consume_events_and_render(history_snapshot, (event for event in events))

    def _get_assistant_input_and_run_commands(self) -> Generator[Event, None, None]:
        if self.assistant_participant.is_agent_mode_enabled():
            yield from self._get_assistant_input_and_run_commands_for_agent()
        else:
            yield from self.assistant_participant.get_input_and_run_commands()

    def _get_assistant_input_and_run_commands_for_agent(self) -> Generator[Event, None, None]:
        yield from self.assistant_participant.get_input_and_run_commands()
        while not self._received_assistant_done_event:
            continuation_event = self._get_agent_continuation_event_from_user()
            history_snapshot = self.history.get_history_for(self.assistant_participant.get_name())
            self._track_events_in_history([continuation_event])
            self.assistant_participant.consume_events_and_render(history_snapshot, (event for event in [continuation_event]))
            yield from self.assistant_participant.get_input_and_run_commands()

    def _get_agent_continuation_event_from_user(self) -> Event:
        continuation_msg = TextMessage(
            author="user",
            text="AUTOMATIC RESPONSE: No ///done command found in your repsonse. "
            "Please continue, and use ///done command when you finish with the whole task.",
            is_directly_entered=True,
        )
        return MessageEvent(continuation_msg)

    def _consume_events_from_assistant_and_render_user(self, events: Generator[Event, None, None]):
        events = self._swallow_engine_commands_from_stream(events)
        events = self._track_events_in_history(events)
        history_snapshot = self.history.get_history_for(self.user_participant.get_name())
        self.user_participant.consume_events_and_render(history_snapshot, events)

    def _commit_history(self):
        self.history.commit()

    def _track_events_in_history(self, events: Iterable[Event]) -> Generator[Event, None, None]:
        for event in events:
            if isinstance(event, MessageEvent):
                self.history.add_message(event.get_message())
            elif isinstance(event, RawContentForHistoryEvent):
                self.history.add_raw_content(event)
            yield event

    def _handle_interruption(self):
        if self.history.reset_uncommitted():
            self.notifications_printer.print_notification(
                "Reset uncommitted changes from interrupted operation",
                CLIColors.YELLOW,
            )

    def _swallow_engine_commands_from_stream(self, stream: Iterable[Event]) -> Generator[Event, None, None]:
        for event in stream:
            if isinstance(event, EngineCommandEvent):
                event.execute(self)
                continue
            yield event

    def _handle_save_history(self, event: SaveHistoryEvent) -> None:
        self.notifications_printer.print_notification(f"Saving history to {event.filepath}")
        self.history.save(event.filepath)

    @property
    def received_assistant_done_event(self) -> bool:
        return self._received_assistant_done_event

    @property
    def should_exit_after_one_cycle(self) -> bool:
        return self._should_exit_after_one_cycle
