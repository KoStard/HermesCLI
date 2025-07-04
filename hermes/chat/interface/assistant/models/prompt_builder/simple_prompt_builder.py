from .base import PromptBuilder, PromptBuilderFactory


class SimplePromptTextPiece:
    def __init__(self, text: str, name: str | None = None, text_role: str | None = None):
        self.text = text
        self.name = name
        self.text_role = text_role


class SimplePromptBuilder(PromptBuilder):
    """A simple prompt builder that concatenates text pieces with empty lines between them."""

    def __init__(self):
        self.text_pieces: list[SimplePromptTextPiece] = []

    def add_text(self, text: str, name: str | None = None, text_role: str | None = None):
        """Adds a piece of text to the prompt.

        Args:
            text (str): The text to add
            name (str, optional): Name identifier for the text piece (unused in simple builder)
            text_role (str, optional): Role of the text (unused in simple builder)
        """
        self.text_pieces.append(SimplePromptTextPiece(text.strip(), name, text_role))

    def compile_prompt(self) -> str:
        """Compiles all added text pieces into a single prompt.

        Returns:
            str: The compiled prompt with empty lines between text pieces
        """
        if not self.text_pieces:
            return ""

        result = []
        for piece in self.text_pieces:
            tag_attrs = []
            if piece.name:
                tag_attrs.append(f'name="{piece.name}"')
            if piece.text_role:
                tag_attrs.append(f'role="{piece.text_role}"')

            tag_start = f"<text {' '.join(tag_attrs)}>" if tag_attrs else "<text>"

            result.append(f"{tag_start}\n{piece.text}\n</text>")

        return "\n\n".join(result)


class SimplePromptBuilderFactory(PromptBuilderFactory):
    def create_prompt_builder(self) -> PromptBuilder:
        return SimplePromptBuilder()
