import mistune
from mistune.renderers.markdown import MarkdownRenderer
from pygments import highlight
from pygments.lexers import get_lexer_by_name, MarkdownLexer
from pygments.formatters import Terminal256Formatter


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

    def process_markdown(self, markdown_text):
        ast = mistune.create_markdown(renderer="ast")
        parsed = ast(markdown_text)
        
        for element in parsed:
            self.print_markdown(self.render_to_markdown(element), self.get_lexer(element))
