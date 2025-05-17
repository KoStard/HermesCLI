from prompt_toolkit.completion import Completer, Completion


class CommandCompleter(Completer):
    def __init__(self, commands: list[str]):
        self.commands = commands

    def fuzzy_match(self, pattern: str, command: str) -> tuple[bool, float]:
        """
        Returns (is_match, score) where:
        - is_match is True if pattern chars appear in order in command
        - score is lower for better matches (consecutive chars score better)
        """
        if not pattern or not command:
            return False, float("inf")

        pattern = pattern.lower()
        command = command.lower()

        score = 0
        last_idx = -1

        for char in pattern:
            # Find the next occurrence of pattern char after last matched position
            try:
                idx = command.index(char, last_idx + 1)
            except ValueError:
                return False, float("inf")

            if last_idx != -1:
                # Add gap penalty
                score += idx - last_idx - 1

            last_idx = idx

        return True, score

    def get_completions(self, document, complete_event):
        text = document.text
        latest_line = text.split("\n")[-1].strip()
        if not latest_line.startswith("/"):
            return

        # Remove the leading slash for matching
        search_text = latest_line[1:]

        # Get all matches with scores
        matches = []
        for command in self.commands:
            # Remove leading slash from command for comparison
            cmd = command[1:] if command.startswith("/") else command
            is_match, score = self.fuzzy_match(search_text, cmd)
            if is_match:
                matches.append((score, command))

        # Sort by score and yield completions
        for _, command in sorted(matches):
            yield Completion(command, start_position=-len(latest_line))
