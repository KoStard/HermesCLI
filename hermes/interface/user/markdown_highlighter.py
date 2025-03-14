import mistune
from mistune.renderers.markdown import MarkdownRenderer
from pygments import highlight
from pygments.lexers import get_lexer_by_name, MarkdownLexer
from pygments.formatters import Terminal256Formatter
from typing import Generator
import pygments


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
            try:
                return get_lexer_by_name(info)
            except pygments.util.ClassNotFound:
                return MarkdownLexer()
        else:
            return MarkdownLexer()

    def print_markdown(self, text, lexer):
        highlighted = highlight(text, lexer, Terminal256Formatter())
        print(highlighted, end="")

    def line_aggregator(
        self, generator: Generator[str, None, None]
    ) -> Generator[str, None, None]:
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

        def _iter_render(tokens, state):
            """
            Fix to a bug where some characters get serialised:
            Test:
                ⋊  python -c 'from hermes.utils.markdown_highlighter import MarkdownHighlighter; print(MarkdownHighlighter().process_markdown("`<>!@#$%^&*()-=`"))'
                `<>!@#$%^&*()-=` < correct
                `&lt;&gt;!@#$%^&amp;*()-=` < incorrect
            """
            for tok in tokens:
                if "children" in tok:
                    children = _iter_render(tok["children"], state)
                    tok["children"] = list(children)
                elif "text" in tok:
                    text = tok.pop("text")
                    tok["children"] = [{"type": "text", "raw": text.strip(" \r\n\t\f")}]
                yield tok

        ast._iter_render = _iter_render
        buffer = ""
        old_parsed = []
        original_text = ""
        output_text = ""

        for line in self.line_aggregator(markdown_generator):
            original_text += line
            buffer += line
            parsed = ast(buffer)
            if len(parsed) == len(old_parsed):
                continue
            old_parsed = parsed
            buffer = line
            while len(parsed) > 1:
                element = parsed.pop(0)
                rendered = self.render_to_markdown(element)
                self.print_markdown(rendered, self.get_lexer(element))
                output_text += rendered
        if buffer:
            parsed = ast(buffer)
            for element in parsed:
                rendered = self.render_to_markdown(element)
                self.print_markdown(rendered, self.get_lexer(element))
                output_text += rendered

        return original_text
