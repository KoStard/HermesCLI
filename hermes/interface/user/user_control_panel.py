import shlex
from argparse import ArgumentParser, Namespace
from typing import Generator
from ..control_panel.base_control_panel import ControlPanel, ControlPanelCommand
from ..helpers.peekable_generator import PeekableGenerator, iterate_while
from hermes.message import ImageUrlMessage, Message, TextGeneratorMessage, TextMessage, ImageMessage, AudioFileMessage, VideoMessage, EmbeddedPDFMessage, TextualFileMessage, UrlMessage
from hermes.event import Event, ExitEvent, LoadHistoryEvent, MessageEvent, ClearHistoryEvent, SaveHistoryEvent, AgentModeEvent
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.utils.tree_generator import TreeGenerator
from hermes.utils.file_extension import remove_quotes
import os

from argparse import ArgumentParser, Namespace
from typing import Generator
from ..control_panel.base_control_panel import ControlPanel, ControlPanelCommand
from ..helpers.peekable_generator import PeekableGenerator, iterate_while
from hermes.message import ImageUrlMessage, Message, TextGeneratorMessage, TextMessage, ImageMessage, AudioFileMessage, VideoMessage, EmbeddedPDFMessage, TextualFileMessage, UrlMessage
from hermes.event import Event, ExitEvent, LoadHistoryEvent, MessageEvent, ClearHistoryEvent, SaveHistoryEvent
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.utils.tree_generator import TreeGenerator

class UserControlPanel(ControlPanel):
    def __init__(self, *, notifications_printer: CLINotificationsPrinter, extra_commands: list[ControlPanelCommand] = None):
        super().__init__()
        self.tree_generator = TreeGenerator()
        self._cli_arguments = set()  # Track which arguments were added to CLI
        self.notifications_printer = notifications_printer
        
        # Register core commands
        self._register_core_commands()
        
        # Register file sharing commands
        self._register_file_commands()
        
        # Register history management commands
        self._register_history_commands()
        
        # Register utility commands
        self._register_utility_commands()
        
        # Add any extra commands provided
        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

    def _register_core_commands(self):
        """Register basic text and exit commands"""
        self._register_command(
            ControlPanelCommand(
                command_id="text",
                command_label="/text",
                description="Add text to the conversation",
                short_description="Send a text message",
                parser=lambda line: MessageEvent(
                    TextMessage(
                        author="user",
                        text=line,
                        is_directly_entered=True
                    )
                )
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="exit",
                command_label="/exit",
                description="Exit the application",
                short_description="Exit Hermes",
                parser=lambda _: ExitEvent(),
                priority=-100  # Run exit after running any other command
            )
        )

    def _register_file_commands(self):
        """Register commands for sharing different file types"""
        self._register_command(
            ControlPanelCommand(
                command_id="image",
                command_label="/image",
                description="Add image to the conversation",
                short_description="Share an image file",
                parser=lambda line: MessageEvent(
                    ImageMessage(
                        author="user",
                        image_path=line
                    )
                )
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="image_url",
                command_label="/image_url",
                description="Add image from url to the conversation",
                short_description="Share an image via URL",
                parser=lambda line: MessageEvent(
                    ImageUrlMessage(
                        author="user",
                        image_url=line
                    )
                )
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="audio",
                command_label="/audio",
                description="Add audio to the conversation",
                short_description="Share an audio file",
                parser=lambda line: MessageEvent(
                    AudioFileMessage(
                        author="user",
                        audio_filepath=line
                    )
                )
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="video",
                command_label="/video",
                description="Add video to the conversation",
                short_description="Share a video file",
                parser=lambda line: MessageEvent(
                    VideoMessage(
                        author="user",
                        video_filepath=line
                    )
                )
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="pdf",
                command_label="/pdf",
                description="Add pdf to the conversation. After the PDF path, optionally use {<page_number>, <page_number>:<page_number>, ...} to specify pages.",
                short_description="Share a PDF file",
                parser=lambda line: MessageEvent(
                    EmbeddedPDFMessage.build_from_line(
                        author="user",
                        raw_line=line
                    )
                )
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="textual_file",
                command_label="/textual_file",
                description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
                short_description="Share a text-based document",
                parser=lambda line: MessageEvent(
                    TextualFileMessage(
                        author="user",
                        text_filepath=line
                    )
                ),
                default_on_cli=True
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="url",
                command_label="/url",
                description="Add url to the conversation",
                short_description="Share a URL",
                parser=lambda line: MessageEvent(
                    UrlMessage(
                        author="user",
                        url=line
                    )
                )
            )
        )

    def _register_history_commands(self):
        """Register commands for managing conversation history"""
        self._register_command(
            ControlPanelCommand(
                command_id="clear",
                command_label="/clear",
                description="Clear the conversation history",
                short_description="Clear chat history",
                parser=lambda _: ClearHistoryEvent(),
                priority=99,  # Clear history should be first
                visible_from_cli=False
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="save_history",
                command_label="/save_history",
                description="Save history to a file",
                short_description="Save chat history",
                parser=lambda line: SaveHistoryEvent(line),
                visible_from_cli=False
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="load_history",
                command_label="/load_history",
                description="Load history from a file",
                short_description="Load chat history",
                parser=lambda line: LoadHistoryEvent(line),
                priority=98
            )
        )

    def _register_utility_commands(self):
        """Register utility commands like directory tree generation"""
        self._register_command(
            ControlPanelCommand(
                command_id="tree",
                command_label="/tree",
                description="Generate a directory tree",
                short_description="Show directory structure",
                parser=self._parse_tree_command
            )
        )
        
        self._register_command(
            ControlPanelCommand(
                command_id="agent_mode",
                command_label="/agent_mode",
                description="Enable or disable agent mode (on/off)",
                short_description="Toggle agent mode",
                parser=lambda line: AgentModeEvent(enabled=line.strip().lower() == "on")
            )
        )

    def render(self):
        return "\n".join(self._render_command_in_control_panel(command) for command in self.commands)

    def break_down_and_execute_message(self, message: Message) -> Generator[Event, None, None]:
        peekable_generator = PeekableGenerator(self._lines_from_message(message))
        prioritised_backlog = []
        # Collecting the text message, can be interrupted by commands
        current_message_text = ""
        for line in peekable_generator:
            matching_command = self._line_command_match(line)
            if matching_command:
                if current_message_text:
                    prioritised_backlog.append((0, MessageEvent(TextMessage(author="user", text=current_message_text, is_directly_entered=True))))
                    current_message_text = ""
                
                command_priority = self.commands[matching_command].priority
                command_parser = self.commands[matching_command].parser
                command_content = self._extract_command_content_in_line(matching_command, line)

                self.notifications_printer.print_notification(f"Command {matching_command} received")

                try:
                    parsed_command_event = command_parser(command_content)
                except Exception as e:
                    self.notifications_printer.print_error(f"Command {matching_command} failed: {e}")
                    continue

                if not isinstance(parsed_command_event, Event):
                    self.notifications_printer.print_error(f"Command {matching_command} returned a non-event object: {parsed_command_event}")
                    continue

                prioritised_backlog.append((command_priority, parsed_command_event))
            else:
                current_message_text += line

        if current_message_text:
            prioritised_backlog.append((0, MessageEvent(TextMessage(author="user", text=current_message_text, is_directly_entered=True))))

        # Highest priority first
        for _, event in sorted(prioritised_backlog, key=lambda x: -x[0]):
            yield event

    def get_command_labels(self) -> list[str]:
        return [command_label for command_label in self.commands]

    def build_cli_arguments(self, parser: ArgumentParser):
        for command_label in self.get_command_labels():
            if self.commands[command_label].visible_from_cli:
                if self.commands[command_label].default_on_cli:
                    parser.add_argument(command_label[1:], type=str, nargs='*', help=self.commands[command_label].description)
                    self._cli_arguments.add(command_label[1:])
                parser.add_argument('--' + command_label[1:], type=str, action="append", help=self.commands[command_label].description)
                self._cli_arguments.add(command_label[1:])
        
        parser.add_argument('--prompt', type=str, action="append", help="Prompt for the LLM")
        self._cli_arguments.add('prompt')

    def convert_cli_arguments_to_text(self, parser: ArgumentParser, args: Namespace) -> str:
        lines = []
        args_dict = vars(args)
        for arg, value in args_dict.items():
            if value is not None and arg in self._cli_arguments:
                if arg != "prompt":
                    for v in value:
                        lines.append(f"/{arg} {v}")
                else:
                    for v in value:
                        lines.append(v)
        return "\n".join(lines)
    
    def _parse_tree_command(self, content: str) -> MessageEvent:
        """
        Parse the /tree command and generate a directory tree.
        
        Args:
            content: The command content after the label
            
        Returns:
            MessageEvent with the tree structure
        """
        # Handle quoted paths with spaces
        parts = shlex.split(content)
        
        path = os.getcwd() if not parts else remove_quotes(parts[0])
        depth = int(parts[1]) if len(parts) > 1 else None
        
        tree_string = self.tree_generator.generate_tree(path, depth)
        tree_message = TextMessage(author="user", text=tree_string)
        return MessageEvent(tree_message)
