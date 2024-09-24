import mistune
from mistune.renderers.markdown import MarkdownRenderer
from pygments import highlight
from pygments.lexers import get_lexer_by_name, MarkdownLexer
from pygments.formatters import Terminal256Formatter
from typing import Generator


class MarkdownHighlighter:
    def __init__(self):
        self.renderer = MarkdownRenderer()
        self.state = mistune.BlockState()

    def render_to_markdown(self, element):
        rendered = self.renderer([element], self.state)
        return rendered

    def get_lexer(self, element):
        info = element.get("attrs", {}).get("info", "")
        if info:
            return get_lexer_by_name(info)
        else:
            return MarkdownLexer()

    def print_markdown(self, text, lexer):
        highlighted = highlight(text, lexer, Terminal256Formatter())
        print(highlighted, end="")

    def line_aggregator(self, generator: Generator[str, None, None]) -> Generator[str, None, None]:
        buffer = ""
        for chunk in generator:
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line + "\n"
        if buffer:
            yield buffer

    def process_markdown(self, markdown_generator: Generator[str, None, None]):
        ast = mistune.create_markdown(renderer="ast")
        buffer = ""
        old_parsed = []

        for line in self.line_aggregator(markdown_generator):
            buffer += line
            parsed = ast(buffer)
            if len(parsed) == len(old_parsed):
                continue
            old_parsed = parsed
            buffer = line
            while len(parsed) > 1:
                element = parsed.pop(0)
                self.print_markdown(self.render_to_markdown(element), self.get_lexer(element))
        if buffer:
            parsed = ast(buffer)
            for element in parsed:
                self.print_markdown(self.render_to_markdown(element), self.get_lexer(element))
