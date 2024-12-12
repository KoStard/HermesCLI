from asyncio import Event
import os
import logging
from typing import Generator
from hermes.event import ClearHistoryEvent, CreateFileEvent, EngineCommandEvent, ExitEvent, LoadHistoryEvent, MessageEvent, SaveHistoryEvent
from hermes.interface.control_panel.peekable_generator import PeekableGenerator
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.participants import Participant
from hermes.history import History
from itertools import cycle, chain

logger = logging.getLogger(__name__)

class Engine:
    def __init__(self, participants: list[Participant], history: History):
        self.participants = participants
        self.history = history
        self.notifications_printer = CLINotificationsPrinter()

    def run(self):
        participants_cycle = cycle(self.participants)
        current_participant = None
        next_participant = next(participants_cycle)

        events_stream_without_engine_commands = []
        
        try:
            while True:
                current_participant, next_participant = next_participant, next(participants_cycle)
                consumption_events = current_participant.consume_events(self._extend_with_history_and_save(events_stream_without_engine_commands))

                # TODO: Check if the error is somewhere here.
                action_events_stream = current_participant.act()
                events_stream = chain(consumption_events, action_events_stream)

                # Make sure there is at least one event in the stream before moving to the next participant. Use peek method.
                events_stream = PeekableGenerator(events_stream)
                logger.debug("Peeking for the first time", current_participant)
                events_stream.peek()
                
                events_stream_without_engine_commands = self._handle_engine_commands_from_stream(events_stream)
        except Exception as e:
            if not isinstance(e, EOFError) and not isinstance(e, KeyboardInterrupt):
                self._handle_save_history_event(SaveHistoryEvent())
            raise e

    def _extend_with_history_and_save(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        """
        Extend the events stream with the history events.

        """
        history_yielded = False
        for event in events:
            """
            Wait for the first event to come, but then first yield all history events before yielding the actual events.
            """
            if not history_yielded:
                for history_event in self.history.get_messages_as_events():
                    yield history_event
                history_yielded = True
            
            if isinstance(event, MessageEvent):
                self.history.add_message(event.get_message())
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
        Create a file with the given content.
        
        Args:
            file_path: Path where to create the file
            content: Content to write to the file
        """
        self.notifications_printer.print_notification(f"Creating file {file_path}")
        with open(file_path, "w") as file:
            file.write(content)
