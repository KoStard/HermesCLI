from asyncio import Event
import os
import logging
from typing import Generator
from hermes.event import ClearHistoryEvent, CreateFileEvent, EngineCommandEvent, ExitEvent, LoadHistoryEvent, MessageEvent, RawContentForHistoryEvent, SaveHistoryEvent
from hermes.interface.control_panel.peekable_generator import PeekableGenerator
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
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

    def run(self):
        while True:
            try:
                self._run_cycle()
            except Exception as e:
                print("Exception")
                if isinstance(e, KeyboardInterrupt):
                    continue
                if isinstance(e, EOFError):
                    return
                self._handle_save_history_event(SaveHistoryEvent())
                raise e
        
    def _run_cycle(self):
        events_stream_without_engine_commands = []
        
        while True:
            # Handle user events and engine commands
            user_participant = self.user_participant
            history_snapshot = self.history.get_history_for(user_participant.get_name())
            consumption_events = user_participant.consume_events(history_snapshot, self._save_to_history(events_stream_without_engine_commands))

            action_events_stream = user_participant.act()
            events_stream = chain(consumption_events, action_events_stream)

            # Make sure there is at least one event in the stream before moving to the next participant. Use peek method.
            events_stream = PeekableGenerator(events_stream)
            logger.debug("Peeking for the first time", user_participant)
            events_stream.peek()
            
            # As user events don't come async, and we can't make the LLM request before finishing the user side, waiting for the user events to come.
            # This is also important as user events can impact the past history
            events_stream_without_engine_commands = list(self._handle_engine_commands_from_stream(events_stream))

            # Handle assistant events
            assistant_participant = self.assistant_participant
            history_snapshot = self.history.get_history_for(assistant_participant.get_name())
            consumption_events = assistant_participant.consume_events(history_snapshot, self._save_to_history(events_stream_without_engine_commands))

            action_events_stream = assistant_participant.act()
            events_stream = chain(consumption_events, action_events_stream)

            # Make sure there is at least one event in the stream before moving to the next participant. Use peek method.
            events_stream = PeekableGenerator(events_stream)
            logger.debug("Peeking for the first time", assistant_participant)
            events_stream.peek()
            
            events_stream_without_engine_commands = self._handle_engine_commands_from_stream(events_stream)

    def _save_to_history(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        for event in events:
            if isinstance(event, MessageEvent):
                self.history.add_message(event.get_message())
            elif isinstance(event, RawContentForHistoryEvent):
                self.history.add_raw_content(event)
            yield event

    def _handle_engine_commands_from_stream(self, stream: Generator[Event, None, None]) -> Generator[Event, None, None]:
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
                elif isinstance(event, CreateFileEvent):
                    if not self._confirm_file_creation(event.file_path):
                        continue
                    
                    self._ensure_directory_exists(event.file_path)
                    self._create_file(event.file_path, event.content)
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
