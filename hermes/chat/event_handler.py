from collections.abc import Generator

from hermes.chat.event import (
    AgentModeEvent,
    AssistantDoneEvent,
    ClearHistoryEvent,
    DeepResearchBudgetEvent,
    EngineCommandEvent,
    Event,
    ExitEvent,
    FileEditEvent,
    LLMCommandsExecutionEvent,
    LoadHistoryEvent,
    OnceEvent,
    SaveHistoryEvent,
    ThinkingLevelEvent,
)
from hermes.chat.file_operations_handler import FileOperationsHandler
from hermes.chat.history import History
from hermes.chat.interface.helpers.cli_notifications import CLIColors, CLINotificationsPrinter
from hermes.chat.participants import Participant


class EventHandler:
    def __init__(
        self,
        notifications_printer: CLINotificationsPrinter,
        file_operations_handler: FileOperationsHandler,
        history: History,
        participants: list[Participant],
        assistant_participant: Participant,
    ):
        self.notifications_printer = notifications_printer
        self.file_operations_handler = file_operations_handler
        self.history = history
        self.participants = participants
        self.assistant_participant = assistant_participant
        self._received_assistant_done_event = False
        self._once_mode = False

        self._event_handlers = self._build_event_handler_map()

    def handle_engine_commands_from_stream(self, stream: Generator[Event, None, None]) -> Generator[Event, None, None]:
        for event in stream:
            if isinstance(event, EngineCommandEvent):
                self._handle_engine_command(event)
                continue
            yield event

    def _build_event_handler_map(self):
        return {
            ClearHistoryEvent: self._handle_clear_history,
            SaveHistoryEvent: self._handle_save_history,
            LoadHistoryEvent: self._handle_load_history,
            ExitEvent: self._handle_exit,
            AgentModeEvent: self._handle_agent_mode,
            AssistantDoneEvent: self._handle_assistant_done,
            LLMCommandsExecutionEvent: self._handle_llm_commands_execution,
            OnceEvent: self._handle_once_mode,
            ThinkingLevelEvent: self._handle_thinking_level,
            DeepResearchBudgetEvent: self._handle_deep_research_budget,
            FileEditEvent: self._handle_file_edit,
        }

    def _handle_engine_command(self, event: EngineCommandEvent) -> None:
        event_type = type(event)
        handler = self._event_handlers.get(event_type)

        if handler:
            if event_type in [
                SaveHistoryEvent,
                LoadHistoryEvent,
                AgentModeEvent,
                LLMCommandsExecutionEvent,
                OnceEvent,
                ThinkingLevelEvent,
                DeepResearchBudgetEvent,
                FileEditEvent,
            ]:
                handler(event)
            else:
                handler()
        else:
            print(f"Unknown engine command, skipping: {event}")

    def _handle_clear_history(self) -> None:
        self.notifications_printer.print_notification("Clearing history")
        self.history.clear()
        for participant in self.participants:
            participant.clear()

    def _handle_save_history(self, event: SaveHistoryEvent) -> None:
        self.notifications_printer.print_notification(f"Saving history to {event.filepath}")
        self.history.save(event.filepath)

    def _handle_load_history(self, event: LoadHistoryEvent) -> None:
        self.notifications_printer.print_notification(f"Loading history from {event.filepath}")
        self.history.load(event.filepath)
        for participant in self.participants:
            participant.initialize_from_history(self.history)

    def _handle_exit(self) -> None:
        raise EOFError

    def _handle_agent_mode(self, event: AgentModeEvent) -> None:
        if event.enabled:
            self.assistant_participant.get_interface().control_panel.enable_agent_mode()
            self.notifications_printer.print_notification("Agent mode enabled")
        else:
            self.assistant_participant.get_interface().control_panel.disable_agent_mode()
            self.notifications_printer.print_notification("Agent mode disabled")

    def _handle_assistant_done(self) -> None:
        self.notifications_printer.print_notification("Assistant marked task as done")
        self._received_assistant_done_event = True

    def _handle_llm_commands_execution(self, event: LLMCommandsExecutionEvent) -> None:
        self.assistant_participant.get_interface().control_panel.set_commands_parsing_status(event.enabled)
        status = "enabled" if event.enabled else "disabled"
        self.notifications_printer.print_notification(f"LLM command execution {status}")

    def _handle_once_mode(self, event: OnceEvent) -> None:
        self._once_mode = event.enabled
        status = "enabled" if event.enabled else "disabled"
        self.notifications_printer.print_notification(f"Once mode {status}")

    def _handle_thinking_level(self, event: ThinkingLevelEvent) -> None:
        self.assistant_participant.get_interface().change_thinking_level(event.level)
        self.notifications_printer.print_notification(f"Thinking level set to {event.level}")

    def _handle_deep_research_budget(self, event: DeepResearchBudgetEvent) -> None:
        if hasattr(self.assistant_participant.get_interface(), "set_budget"):
            self.assistant_participant.get_interface().set_budget(event.budget)
            self.notifications_printer.print_notification(f"Deep Research budget set to {event.budget} message cycles")
        else:
            self.notifications_printer.print_notification(
                "Budget setting is only available for Deep Research Assistant",
                CLIColors.YELLOW,
            )

    def _handle_file_edit(self, event: FileEditEvent) -> None:
        if event.mode == "create":
            self.file_operations_handler.create_file(event.file_path, event.content)
        elif event.mode == "append":
            self.file_operations_handler.append_to_file(event.file_path, event.content)
        elif event.mode == "update_markdown_section":
            self.file_operations_handler.update_markdown_section(
                event.file_path,
                event.section_path,
                event.content,
                event.submode,
            )
        elif event.mode == "prepend":
            self.file_operations_handler.handle_file_prepend(event.file_path, event.content)

    @property
    def received_assistant_done_event(self) -> bool:
        return self._received_assistant_done_event

    @received_assistant_done_event.setter
    def received_assistant_done_event(self, value: bool) -> None:
        self._received_assistant_done_event = value

    @property
    def once_mode(self) -> bool:
        return self._once_mode

    @once_mode.setter
    def once_mode(self, value: bool) -> None:
        self._once_mode = value
