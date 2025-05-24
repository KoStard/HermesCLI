from prompt_toolkit.completion import Completer

from hermes.chat.interface.user.interface.command_completer.completion_generator import CompletionGenerator


class CommandCompleter(Completer):
    def __init__(self, commands: list[str]):
        self.completion_generator = CompletionGenerator(commands)

    def get_completions(self, document, complete_event):
        text = document.text
        latest_line = text.split("\n")[-1].strip()

        if not self._is_command_line(latest_line):
            return

        search_text = self._extract_search_text(latest_line)
        start_position = -len(latest_line)

        yield from self.completion_generator.generate_completions(search_text, start_position)

    def _is_command_line(self, line: str) -> bool:
        return line.startswith("/")

    def _extract_search_text(self, line: str) -> str:
        return line[1:]
