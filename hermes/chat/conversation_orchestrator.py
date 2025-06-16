import logging
import sys
from collections.abc import Generator, Iterable
from itertools import chain
from typing import TYPE_CHECKING

from hermes.chat.events.base import Event
from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.events.engine_commands.save_history import SaveHistoryEvent
from hermes.chat.events.history_recovery_event import HistoryRecoveryEvent
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.file_operations_handler import FileOperationsHandler
from hermes.chat.history import History
from hermes.chat.interface.assistant.chat.assistant_orchestrator import ChatAssistantOrchestrator
from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
from hermes.chat.interface.helpers.cli_notifications import CLIColors, CLINotificationsPrinter
from hermes.chat.messages.text import InvisibleMessage
from hermes.chat.participants import DebugParticipant, LLMParticipant, Participant

if TYPE_CHECKING:
    from hermes.mcp.mcp_manager import McpManager

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    def __init__(
        self,
        user_participant: Participant,
        assistant_participant: LLMParticipant | DebugParticipant,
        history: History,
        mcp_manager: "McpManager",
    ):
        self.user_participant = user_participant
        self.assistant_participant = assistant_participant
        self.participants = [self.user_participant, self.assistant_participant]
        self.history = history
        self.notifications_printer = CLINotificationsPrinter()
        self.mcp_manager = mcp_manager

        self.file_operations_handler = FileOperationsHandler(self.notifications_printer)
        self._received_assistant_done_event = False
        self._should_exit_after_one_cycle = False
        self._mcp_commands_added = False

    def start_conversation(self):
        try:
            self._start_conversation_loop()
        except EOFError as e:
            raise e
        except Exception as e:
            self._handle_save_history(SaveHistoryEvent())
            raise e

    def _start_conversation_loop(self):
        self._handle_mcp_status()
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

    def _get_user_input_and_run_commands(self) -> Generator[Event, None, None]:
        return self.user_participant.get_input_and_run_commands()

    def _consume_events_from_user_and_render_assistant(self, events: Generator[Event, None, None]):
        self.assistant_participant.prepare()
        all_events = list(self._swallow_engine_commands_from_stream(events))
        # Ensure MCPs are fully loaded before sending messages to the assistant
        self._wait_for_mcps_and_update_commands()
        history_recovery_event = HistoryRecoveryEvent(self.history.get_history_for(self.assistant_participant.get_name()))
        all_events = list(self._track_events_in_history(all_events))
        all_events.insert(0, history_recovery_event)
        self.assistant_participant.consume_events_and_render(event for event in all_events)

    def _get_assistant_input_and_run_commands(self) -> Generator[Event, None, None]:
        if self.assistant_participant.is_agent_mode_enabled():
            yield from self._get_assistant_input_and_run_commands_for_agent()
        else:
            yield from self.assistant_participant.get_input_and_run_commands()

    def _get_assistant_input_and_run_commands_for_agent(self) -> Generator[Event, None, None]:
        yield from self.assistant_participant.get_input_and_run_commands()
        while not self._received_assistant_done_event:
            continuation_event = self._get_agent_continuation_event_from_user()
            history_snapshot = HistoryRecoveryEvent(self.history.get_history_for(self.assistant_participant.get_name()))
            self._track_events_in_history([continuation_event])
            self.assistant_participant.consume_events_and_render(event for event in [history_snapshot, continuation_event])
            yield from self.assistant_participant.get_input_and_run_commands()

    def _get_agent_continuation_event_from_user(self) -> Event:
        continuation_msg = InvisibleMessage(
            author="user",
            text="""AUTOMATIC RESPONSE: I see you're still working on this task. Please continue with your next steps.

A few reminders to help you:
- When you've completed the entire task, use the done command with your final report
- You can run multiple commands in a single response for better efficiency
- If you need to split complex work, consider creating subtasks
- Remember to always verify your results before marking the task as done

If you encounter any system issues or need to halt execution for any reason, you can use the emergency code "SHUT_DOWN_DEEP_RESEARCHER".

I'll wait for your next steps or completion message.""",
            is_directly_entered=True,
        )
        return MessageEvent(continuation_msg)

    def _consume_events_from_assistant_and_render_user(self, events: Generator[Event, None, None]):
        events = self._swallow_engine_commands_from_stream(events)
        history_snapshot = HistoryRecoveryEvent(self.history.get_history_for(self.user_participant.get_name()))
        events = self._track_events_in_history(events)
        self.user_participant.consume_events_and_render(event for event in chain([history_snapshot], events))

    def _commit_history(self):
        self.history.commit()

    def _track_events_in_history(self, events: Iterable[Event]) -> Generator[Event, None, None]:
        for event in events:
            if isinstance(event, MessageEvent):
                self.history.add_message(event.get_message())
            yield event

    def _wait_for_mcps_and_update_commands(self):
        """Wait for MCP clients to load and update commands."""
        if self._mcp_commands_added:
            return
        self._mcp_commands_added = True
        if not self.mcp_manager.initial_load_complete:
            self.notifications_printer.print_notification("Waiting for MCP servers to finish loading...", CLIColors.YELLOW)
            self.mcp_manager.wait_for_initial_load()

        # Update the available commands once loaded
        assistant_interface = self.assistant_participant.orchestrator
        if isinstance(assistant_interface, DeepResearchAssistantOrchestrator | ChatAssistantOrchestrator):
            assistant_interface.update_mcp_commands()

        # Check for errors after loading
        self._handle_mcp_errors()

    def _handle_mcp_status(self):
        """Checks and reports the status of MCP clients."""
        report = self.mcp_manager.get_status_report()
        if report:
            self.notifications_printer.print_notification(report, CLIColors.YELLOW)

    def _handle_mcp_errors(self):
        """Handle errors from MCP clients."""
        # Only proceed if there are errors and they haven't been acknowledged
        if not self.mcp_manager.has_errors() or self.mcp_manager.are_errors_acknowledged():
            return

        error_report = self.mcp_manager.get_error_report()
        self.notifications_printer.print_notification(error_report, CLIColors.RED)
        try:
            # This is a simple way to pause and ask for confirmation.
            # It slightly breaks the UI abstraction but is acceptable for this critical path.
            response = input("Errors occurred with MCP servers. Do you want to continue? (y/n): ").lower()
            if response not in ["y", "yes"]:
                self.notifications_printer.print_notification("Exiting due to MCP errors.", CLIColors.RED)
                sys.exit(1)
            else:
                self.mcp_manager.acknowledge_errors()
        except (EOFError, KeyboardInterrupt):
            self.notifications_printer.print_notification("\nExiting.", CLIColors.YELLOW)
            sys.exit(1)

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

    def set_received_assistant_done_event(self, status: bool):
        self._received_assistant_done_event = status

    @property
    def should_exit_after_one_cycle(self) -> bool:
        return self._should_exit_after_one_cycle

    def set_should_exit_after_one_cycle(self, status: bool):
        self._should_exit_after_one_cycle = status
