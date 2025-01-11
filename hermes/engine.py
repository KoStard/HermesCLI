from asyncio import Event
import os
import logging
from typing import Generator
from hermes.event import AssistantDoneEvent, ClearHistoryEvent, FileEditEvent, EngineCommandEvent, ExitEvent, LoadHistoryEvent, MessageEvent, RawContentForHistoryEvent, SaveHistoryEvent, AgentModeEvent, LLMCommandsExecutionEvent
from hermes.interface.helpers.peekable_generator import PeekableGenerator
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter, CLIColors
from hermes.message import TextMessage
from hermes.participants import Participant
from hermes.history import History
from itertools import cycle, chain
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class Engine:
    def __init__(self, user_participant: Participant, assistant_participant: Participant, history: History):
        self.user_participant = user_participant
        self.assistant_participant = assistant_participant
        self.participants = [self.user_participant, self.assistant_participant]
        self.history = history
        self.notifications_printer = CLINotificationsPrinter()
        self._received_assistant_done_event = False

    def run(self):
        while True:
            try:
                self._run_cycle()
            except KeyboardInterrupt:
                if self.history.reset_uncommitted():
                    self.notifications_printer.print_notification("Reset uncommitted changes from interrupted operation", CLIColors.YELLOW)
                continue
            except EOFError:
                return
            except Exception as e:
                self._handle_save_history_event(SaveHistoryEvent())
                raise e
        
    def _run_cycle(self):
        assistant_events = []
        while True:
            user_events = self._run_user(assistant_events)
            assistant_events = self._run_assistant(user_events)

    def _run_user(self, assistant_events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        """Handle user events and engine commands"""
        history_snapshot = self.history.get_history_for(self.user_participant.get_name())
        consumption_events = self.user_participant.consume_events(history_snapshot, self._save_to_history(assistant_events))
        
        self.history.commit()

        action_events_stream = self.user_participant.act()
        events_stream = chain(consumption_events, action_events_stream)

        # Make sure there is at least one event in the stream before moving to the next participant
        events_stream = PeekableGenerator(events_stream)
        logger.debug("Peeking for the first time", self.user_participant)
        events_stream.peek()
        
        # As user events don't come async, and we can't make the LLM request before finishing the user side
        # Converting to list is also important as user events can impact the past history
        user_events = list(self._handle_engine_commands_from_stream(events_stream))
        return user_events

    def _run_assistant(self, user_events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        """Handle assistant events and agent mode continuation"""
        is_first_cycle = True
        is_llm_turn = True
        
        while is_llm_turn:
            # Add continuation prompt if in agent mode, in all cycles except the first
            if self.assistant_participant.interface.control_panel._agent_mode:
                if not is_first_cycle:
                    continuation_msg = TextMessage(
                        author="user",
                        text="Continue please. When you are done with the task, use the done command to send to the user.",
                        is_directly_entered=True
                    )
                    user_events = [MessageEvent(continuation_msg)]
                is_first_cycle = False
                
            history_snapshot = self.history.get_history_for(self.assistant_participant.get_name())

            consumption_events = self.assistant_participant.consume_events(history_snapshot, self._save_to_history(user_events))
            action_events_stream = self.assistant_participant.act()
            events_stream = chain(consumption_events, action_events_stream)

            # Make sure there is at least one event in the stream
            events_stream = PeekableGenerator(events_stream)
            logger.debug("Peeking for the first time", self.assistant_participant)
            events_stream.peek()
            
            yield from self._handle_engine_commands_from_stream(events_stream)

            # Check if we should continue in agent mode
            if not self.assistant_participant.interface.control_panel._agent_mode:
                is_llm_turn = False
                
            # Check if we received an AssistantDoneEvent
            if self._received_assistant_done_event:
                self._received_assistant_done_event = False
                is_llm_turn = False

    def _save_to_history(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        for event in events:
            if isinstance(event, MessageEvent):
                self.history.add_message(event.get_message())
            elif isinstance(event, RawContentForHistoryEvent):
                self.history.add_raw_content(event)
            yield event

    def _handle_engine_commands_from_stream(self, stream: Generator[Event, None, None]) -> Generator[Event, None, None]:
        """
        Handles engine commands from the stream and emits the rest of the events.
        """
        for event in stream:
            if isinstance(event, EngineCommandEvent):
                if isinstance(event, ClearHistoryEvent):
                    self.notifications_printer.print_notification("Clearing history")
                    self.history.clear()
                    for participant in self.participants:
                        participant.clear()
                elif isinstance(event, SaveHistoryEvent):
                    self._handle_save_history_event(event)
                elif isinstance(event, LoadHistoryEvent):
                    self.notifications_printer.print_notification(f"Loading history from {event.filepath}")
                    self.history.load(event.filepath)
                    for participant in self.participants:
                        participant.initialize_from_history(self.history)
                elif isinstance(event, ExitEvent):
                    self._handle_exit_event()
                elif isinstance(event, AgentModeEvent):
                    if event.enabled:
                        self.assistant_participant.interface.control_panel.enable_agent_mode()
                        self.notifications_printer.print_notification("Agent mode enabled")
                    else:
                        self.assistant_participant.interface.control_panel.disable_agent_mode()
                        self.notifications_printer.print_notification("Agent mode disabled")
                elif isinstance(event, AssistantDoneEvent):
                    self.notifications_printer.print_notification("Assistant marked task as done")
                    self._received_assistant_done_event = True
                    # TODO: Handle the completion report and any cleanup
                elif isinstance(event, LLMCommandsExecutionEvent):
                    self.assistant_participant.interface.control_panel.set_commands_parsing_status(event.enabled)
                    status = "enabled" if event.enabled else "disabled"
                    self.notifications_printer.print_notification(f"LLM command execution {status}")
                elif isinstance(event, FileEditEvent):
                    if event.mode == 'create':
                        if not self._confirm_file_creation(event.file_path):
                            continue
                        self._ensure_directory_exists(event.file_path)
                        self._create_file(event.file_path, event.content)
                    elif event.mode == 'append':
                        self._ensure_directory_exists(event.file_path)
                        self._append_file(event.file_path, event.content)
                    elif event.mode == 'update_markdown_section':
                        self._ensure_directory_exists(event.file_path)
                        self._update_markdown_section(event.file_path, event.section_path, event.content, event.submode)
                    elif event.mode == 'prepend':
                        self._ensure_directory_exists(event.file_path)
                        self._prepend_file(event.file_path, event.content)
                else:
                    print(f"Unknown engine command, skipping: {event}")
                continue
            yield event

    def _handle_save_history_event(self, event: SaveHistoryEvent):
        self.notifications_printer.print_notification(f"Saving history to {event.filepath}")
        self.history.save(event.filepath)

    def _handle_exit_event(self):
        raise EOFError

    def _confirm_file_creation(self, file_path: str) -> bool:
        """
        Check if file exists and ask for confirmation to overwrite if it does.
        
        Args:
            file_path: Path to the file to be created
            
        Returns:
            bool: True if file should be created, False otherwise
        """
        if os.path.exists(file_path):
            self.notifications_printer.print_notification(f"File {file_path} already exists.")
            response = input("Do you want to overwrite it? [y/N] ").strip().lower()
            if response != 'y':
                self.notifications_printer.print_notification("File creation cancelled.")
                return False
        return True
    
    def _backup_existing_file(self, file_path: str) -> None:
        """
        Backup the existing file to prevent possible data loss.
        Copy to the /tmp/hermes/backups/filename_timestamp.bak
        
        Args:
            file_path: Path to the file to be backed up
        """
        if not os.path.exists(file_path):
            return

        # Create backup directory
        backup_dir = os.path.join('/tmp', 'hermes', 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")

        # Create the backup
        shutil.copy2(file_path, backup_path)
        self.notifications_printer.print_notification(f"Created backup at {backup_path}")

    def _ensure_directory_exists(self, file_path: str) -> None:
        """
        Create directory structure for the given file path if it doesn't exist.
        
        Args:
            file_path: Path to the file to be created
        """
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            self.notifications_printer.print_notification(f"Creating directory structure: {directory}")
            os.makedirs(directory, exist_ok=True)

    def _create_file(self, file_path: str, content: str) -> None:
        """
        Create a file with the given content. If file exists, create a backup first.
        
        Args:
            file_path: Path where to create the file
            content: Content to write to the file
        """
        if os.path.exists(file_path):
            self._backup_existing_file(file_path)
        
        self.notifications_printer.print_notification(f"Creating file {file_path}")
        with open(file_path, "w") as file:
            file.write(content)

    def _update_markdown_section(self, file_path: str, section_path: list[str], new_content: str, submode: str) -> None:
        """
        Update a specific section in a markdown file.
        
        Args:
            file_path: Path to the markdown file
            section_path: List of headers leading to target section
            new_content: New content for the section
        """
        from hermes.interface.markdown.document_updater import MarkdownDocumentUpdater
        
        updater = MarkdownDocumentUpdater(file_path)
               
        try:
            was_updated = updater.update_section(section_path, new_content, submode)
            if was_updated:
                action = 'Updated' if submode == 'update_markdown_section' else 'Appended to'
                self.notifications_printer.print_notification(
                    f"{action} section {' > '.join(section_path)} in {file_path}")
            else:
                self.notifications_printer.print_notification(
                    f"Warning: Section {' > '.join(section_path)} not found in {file_path}. No changes made.",
                    color=CLIColors.YELLOW)
        except ValueError as e:
            self.notifications_printer.print_notification(str(e))
            raise

    def _append_file(self, file_path: str, content: str) -> None:
        """
        Append content to a file. Create if doesn't exist.
        
        Args:
            file_path: Path where to append content
            content: Content to append to the file
        """
        mode = "a" if os.path.exists(file_path) else "w"
        action = "Appending to" if mode == "a" else "Creating"
        self.notifications_printer.print_notification(f"{action} file {file_path}")
        with open(file_path, mode) as file:
            file.write(content)

    def _prepend_file(self, file_path: str, content: str) -> None:
        """
        Prepend content to a file. Create if doesn't exist.
        
        Args:
            file_path: Path where to prepend content
            content: Content to prepend to the file
        """
        if os.path.exists(file_path):
            # Read existing content
            with open(file_path, 'r') as file:
                existing_content = file.read()
            # Write new content followed by existing
            with open(file_path, 'w') as file:
                file.write(content + existing_content)
            self.notifications_printer.print_notification(f"Prepending to file {file_path}")
        else:
            # If file doesn't exist, just create it with the content
            with open(file_path, 'w') as file:
                file.write(content)
            self.notifications_printer.print_notification(f"Creating file {file_path}")
