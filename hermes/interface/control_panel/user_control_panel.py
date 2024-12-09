from argparse import ArgumentParser, Namespace
from typing import Generator
from .base_control_panel import ControlPanel, ControlPanelCommand
from .peekable_generator import PeekableGenerator, iterate_while
from hermes.message import ImageUrlMessage, Message, TextGeneratorMessage, TextMessage, ImageMessage, AudioFileMessage, VideoMessage, EmbeddedPDFMessage, TextualFileMessage, UrlMessage
from hermes.event import Event, ExitEvent, LoadHistoryEvent, MessageEvent, ClearHistoryEvent, SaveHistoryEvent
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter

class UserControlPanel(ControlPanel):
    def __init__(self, *, notifications_printer: CLINotificationsPrinter, extra_commands: list[ControlPanelCommand] = None):
        super().__init__()
        self._register_command(ControlPanelCommand(command_label="/clear", description="Clear the conversation history", parser=lambda _: ClearHistoryEvent(), priority=99, visible_from_cli=False)) # Clear history should be the first command, we'll clear then do the rest
        self._register_command(ControlPanelCommand(command_label="/image", description="Add image to the conversation", parser=lambda line: MessageEvent(ImageMessage(author="user", image_path=line))))
        self._register_command(ControlPanelCommand(command_label="/image_url", description="Add image from url to the conversation", parser=lambda line: MessageEvent(ImageUrlMessage(author="user", image_url=line))))
        self._register_command(ControlPanelCommand(command_label="/audio", description="Add audio to the conversation", parser=lambda line: MessageEvent(AudioFileMessage(author="user", audio_filepath=line))))
        self._register_command(ControlPanelCommand(command_label="/video", description="Add video to the conversation", parser=lambda line: MessageEvent(VideoMessage(author="user", video_filepath=line))))
        self._register_command(ControlPanelCommand(command_label="/pdf", description="Add pdf to the conversation. After the PDF path, optionally use {<page_number>, <page_number>:<page_number>, ...} to specify pages.", parser=lambda line: MessageEvent(EmbeddedPDFMessage.build_from_line(author="user", raw_line=line))))
        self._register_command(ControlPanelCommand(command_label="/textual_file", description="Add text file to the conversation", parser=lambda line: MessageEvent(TextualFileMessage(author="user", text_filepath=line)), default_on_cli=True))
        self._register_command(ControlPanelCommand(command_label="/url", description="Add url to the conversation", parser=lambda line: MessageEvent(UrlMessage(author="user", url=line))))
        self._register_command(ControlPanelCommand(command_label="/save_history", description="Save history to a file", parser=lambda line: SaveHistoryEvent(line), visible_from_cli=False))
        self._register_command(ControlPanelCommand(command_label="/load_history", description="Load history from a file", parser=lambda line: LoadHistoryEvent(line), priority=98))
        self._register_command(ControlPanelCommand(command_label="/text", description="Add text to the conversation", parser=lambda line: MessageEvent(TextMessage(author="user", text=line))))
        self._register_command(ControlPanelCommand(command_label="/exit", description="Exit the application", parser=lambda _: ExitEvent(), priority=100))

        if extra_commands:
            for command in extra_commands:
                self._register_command(command)
        
        self.notifications_printer = notifications_printer

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
                    prioritised_backlog.append((0, MessageEvent(TextMessage(author="user", text=current_message_text))))
                    current_message_text = ""
                
                command_priority = self.commands[matching_command].priority
                command_parser = self.commands[matching_command].parser
                command_content = self._extract_command_content_in_line(matching_command, line)
                try:
                    parsed_command_event = command_parser(command_content)
                except Exception as e:
                    self.notifications_printer.print_error(f"Command {matching_command} failed: {e}")
                    continue

                if not isinstance(parsed_command_event, Event):
                    self.notifications_printer.print_error(f"Command {matching_command} returned a non-event object: {parsed_command_event}")
                    continue

                self.notifications_printer.print_notification(f"Command {matching_command} received")

                prioritised_backlog.append((command_priority, parsed_command_event))
            else:
                current_message_text += line

        if current_message_text:
            prioritised_backlog.append((0, MessageEvent(TextMessage(author="user", text=current_message_text))))

        # Highest priority first
        for _, event in sorted(prioritised_backlog, key=lambda x: -x[0]):
            yield event

    def get_command_labels(self) -> list[str]:
        return [command_label for command_label in self.commands]

    def build_cli_arguments(self, parser: ArgumentParser):
        user_commands_group = parser.add_argument_group("User commands")
        for command_label in self.get_command_labels():
            if self.commands[command_label].visible_from_cli:
                if self.commands[command_label].default_on_cli:
                    user_commands_group.add_argument(command_label[1:], type=str, nargs='*', help=self.commands[command_label].description)
                user_commands_group.add_argument('--' + command_label[1:], type=str, action="append", help=self.commands[command_label].description)
        
        user_commands_group.add_argument('--prompt', type=str, action="append", help="Prompt for the LLM")

    def convert_cli_arguments_to_text(self, parser: ArgumentParser, args: Namespace) -> str:
        commands_group = self._get_arguments_by_group(parser, args, "User commands")
        lines = []
        for arg, value in commands_group:
            if arg != "prompt":
                for v in value:
                    lines.append(f"/{arg} {v}")
            else:
                for v in value:
                    lines.append(v)
        return "\n".join(lines)
    
    def _get_arguments_by_group(self, parser: ArgumentParser, args: Namespace, group_name: str) -> tuple[tuple[str, list[str]]]:
        """
        Extract arguments that belong to a specific argument group from parsed command-line arguments.
        
        Args:
            args: Parsed command-line arguments
            group_name: Name of the argument group to extract
            
        Returns:
            Dictionary mapping argument names to their values for the specified group
        """
        # Find the argument group by name
        target_group = None
        for group in parser._action_groups:
            if group.title == group_name:
                target_group = group
                break
                
        if not target_group:
            return tuple()
            
        # Get the argument names (destinations) that belong to this group
        group_arg_names = {action.dest for action in target_group._group_actions}
        
        # Convert args Namespace to dictionary and filter for group arguments
        args_dict = vars(args)
        return tuple(
            (k, v) for k, v in args_dict.items() 
            if k in group_arg_names and v is not None
        )