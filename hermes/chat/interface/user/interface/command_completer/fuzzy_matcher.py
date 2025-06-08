class FuzzyMatcher:
    @staticmethod
    def _check_edge_cases(pattern: str, command: str) -> tuple[bool, float] | None:
        """Checks edge cases and returns result if applicable, None otherwise."""
        if not command:
            return False, float("inf")
        if not pattern:
            return True, float("inf")
        return None

    @staticmethod
    def _find_char_position(char: str, command: str, start_idx: int) -> int | None:
        """Finds the position of a character in the command string starting from start_idx."""
        try:
            return command.index(char, start_idx)
        except ValueError:
            return None

    @staticmethod
    def _calculate_match_score(pattern: str, command: str) -> tuple[bool, float]:
        """Calculate match score based on character positions in command."""
        score = 0
        last_idx = -1

        for char in pattern:
            idx = FuzzyMatcher._find_char_position(char, command, last_idx + 1)
            if idx is None:
                return False, float("inf")

            if last_idx != -1:
                score += idx - last_idx - 1

            last_idx = idx

        return True, score

    @staticmethod
    def match(pattern: str, command: str) -> tuple[bool, float]:
        """Returns (is_match, score) where:
        - is_match is True if pattern chars appear in order in command
        - score is lower for better matches (consecutive chars score better)
        """
        edge_case_result = FuzzyMatcher._check_edge_cases(pattern, command)
        if edge_case_result is not None:
            return edge_case_result

        pattern = pattern.lower()
        command = command.lower()

        return FuzzyMatcher._calculate_match_score(pattern, command)
