class ContentTruncator:
    @staticmethod
    def truncate(content: str, max_length: int, additional_help: str = None) -> str:
        """
        Truncates content to the specified maximum length, ending at a line break.

        Args:
            content: The string content to truncate
            max_length: Maximum length of the truncated content
            additional_help: Optional additional help you want to include in the content

        Returns:
            Truncated content with a note about omitted content if truncation occurred
        """
        if max_length is None or len(content) <= max_length:
            return content

        if type(max_length) is int:
            max_length = int(max_length)

        # Find the last line break before max_length
        last_newline_pos = content[:max_length].rfind("\n")

        # If no newline found, just truncate at max_length
        truncated = content[:max_length] if last_newline_pos == -1 else content[:last_newline_pos]

        # Add a note about how much content was omitted
        omitted_chars = len(content) - len(truncated)
        percentage_omitted = (omitted_chars / len(content)) * 100

        note = f"\n\n[...{omitted_chars:,} characters omitted ({percentage_omitted:.1f}% of content)]"

        if additional_help:
            note += f"\n\nNote: {additional_help}"

        return truncated + note
