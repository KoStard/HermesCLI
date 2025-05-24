class FuzzyMatcher:
    @staticmethod
    def match(pattern: str, command: str) -> tuple[bool, float]:
        """
        Returns (is_match, score) where:
        - is_match is True if pattern chars appear in order in command
        - score is lower for better matches (consecutive chars score better)
        """
        if not command:
            return False, float("inf")
        if not pattern:
            return True, float("inf")

        pattern = pattern.lower()
        command = command.lower()

        score = 0
        last_idx = -1

        for char in pattern:
            try:
                idx = command.index(char, last_idx + 1)
            except ValueError:
                return False, float("inf")

            if last_idx != -1:
                score += idx - last_idx - 1

            last_idx = idx

        return True, score
