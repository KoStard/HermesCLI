from typing import Generator
from .base_control_panel import ControlPanel, ControlPanelCommand
from .peekable_generator import PeekableGenerator, iterate_while
from hermes.message import Message, TextGeneratorMessage, TextMessage
from hermes.event import Event, MessageEvent
class LLMControlPanel(ControlPanel):
    def __init__(self, extra_commands: list[ControlPanelCommand] = None):
        super().__init__()

        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

    def render(self):
        return MessageEvent(TextMessage(author="user", text="\n".join(self._render_command_in_control_panel(command_label) for command_label in self.commands)))

    def break_down_and_execute_message(self, message: Message) -> Generator[Event, None, None]:
        peekable_generator = PeekableGenerator(self._lines_from_message(message))

        while True:
            try:
                line = peekable_generator.peek()
            except StopIteration:
                return

            command_label = self._line_command_match(line)

            if command_label:
                next(peekable_generator) # Consume the line
                yield self.commands[command_label].parser(line)
            else:
                yield MessageEvent(TextGeneratorMessage(author="assistant", text_generator=iterate_while(peekable_generator, lambda line: not self._line_command_match(line)))) 
