import logging
from collections.abc import Generator
from itertools import chain

from hermes.chat.assistant_mode_manager import AssistantModeManager
from hermes.chat.event import Event, MessageEvent, RawContentForHistoryEvent, SaveHistoryEvent
from hermes.chat.event_handler import EventHandler
from hermes.chat.file_operations_handler import FileOperationsHandler
from hermes.chat.history import History
from hermes.chat.interface.helpers.cli_notifications import CLIColors, CLINotificationsPrinter
from hermes.chat.interface.helpers.peekable_generator import PeekableGenerator
from hermes.chat.participants import Participant

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    def __init__(
        self,
        user_participant: Participant,
        assistant_participant: Participant,
        history: History,
    ):
        self.user_participant = user_participant
        self.assistant_participant = assistant_participant
        self.participants = [self.user_participant, self.assistant_participant]
        self.history = history
        self.notifications_printer = CLINotificationsPrinter()

        self.file_operations_handler = FileOperationsHandler(self.notifications_printer)
        self.event_handler = EventHandler(
            self.notifications_printer,
            self.file_operations_handler,
            self.history,
            self.participants,
            self.assistant_participant,
        )
        self.assistant_mode_manager = AssistantModeManager(self.assistant_participant)

    def start_conversation(self):
        while True:
            try:
                self._execute_conversation_cycle()
                if self.event_handler.once_mode:
                    return
            except KeyboardInterrupt:
                self._handle_interruption()
                continue
            except EOFError:
                return
            except Exception as e:
                self.event_handler._handle_save_history(SaveHistoryEvent())
                raise e

    def _execute_conversation_cycle(self):
        assistant_events = []
        while True:
            try:
                once_mode_active = self.event_handler.once_mode
                user_events = self._process_user_turn(assistant_events)
                if once_mode_active:
                    list(user_events)
                    return
                assistant_events = self._process_assistant_turn(user_events)
            except KeyboardInterrupt:
                self._handle_interruption()
                continue
            except EOFError as e:
                raise e
            except Exception as e:
                self.notifications_printer.print_notification(f"Assistant request failed with {e}", CLIColors.RED)
                import traceback

                print(traceback.format_exc())

    def _process_user_turn(self, assistant_events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        history_snapshot = self.history.get_history_for(self.user_participant.get_name())
        consumption_events = self.user_participant.consume_events(history_snapshot, self._track_events_in_history(assistant_events))

        self.history.commit()

        if self.event_handler.once_mode:
            list(consumption_events)
            return []

        action_events_stream = self.user_participant.act()
        events_stream = chain(consumption_events, action_events_stream)

        events_stream = PeekableGenerator(events_stream)
        events_stream.peek()

        user_events = list(self.event_handler.handle_engine_commands_from_stream(events_stream))
        return user_events

    def _process_assistant_turn(self, user_events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        is_first_cycle = True
        continue_assistant_turn = True

        while continue_assistant_turn:
            continuation_events = self.assistant_mode_manager.get_continuation_message_if_needed(is_first_cycle)
            if continuation_events:
                user_events = continuation_events
            is_first_cycle = False

            history_snapshot = self.history.get_history_for(self.assistant_participant.get_name())

            consumption_events = self.assistant_participant.consume_events(history_snapshot, self._track_events_in_history(user_events))
            action_events_stream = self.assistant_participant.act()
            events_stream = chain(consumption_events, action_events_stream)

            events_stream = PeekableGenerator(events_stream)
            events_stream.peek()

            yield from self.event_handler.handle_engine_commands_from_stream(events_stream)

            if not self.assistant_mode_manager.should_continue_assistant_turn():
                continue_assistant_turn = False

            if self.event_handler.received_assistant_done_event:
                self.event_handler.received_assistant_done_event = False
                continue_assistant_turn = False

    def _track_events_in_history(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
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
