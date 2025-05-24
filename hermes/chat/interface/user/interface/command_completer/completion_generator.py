from prompt_toolkit.completion import Completion

from hermes.chat.interface.user.interface.command_completer.fuzzy_matcher import FuzzyMatcher


class CompletionGenerator:
    def __init__(self, commands: list[str]):
        self.commands = commands
        self.fuzzy_matcher = FuzzyMatcher()

    def generate_completions(self, search_text: str, start_position: int):
        matches = self._get_matches(search_text)
        for _, command in sorted(matches):
            yield Completion(command, start_position=start_position)

    def _get_matches(self, search_text: str) -> list[tuple[float, str]]:
        matches = []
        for command in self.commands:
            cmd = self._normalize_command(command)
            is_match, score = self.fuzzy_matcher.match(search_text, cmd)
            if is_match:
                matches.append((score, command))
        return matches

    def _normalize_command(self, command: str) -> str:
        return command[1:] if command.startswith("/") else command
