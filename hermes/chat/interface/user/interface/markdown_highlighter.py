from collections.abc import Generator


class MarkdownHighlighter:
    def __init__(self):
        import mistune
        from mistune.renderers.markdown import MarkdownRenderer

        self.renderer = MarkdownRenderer()
        self.state = mistune.BlockState()

    def render_to_markdown(self, element):
        return self.renderer([element], self.state)

    def get_lexer(self, element):
        import pygments
        from pygments.lexers import MarkdownLexer, get_lexer_by_name

        info = element.get("attrs", {}).get("info", "")
        if info:
            try:
                return get_lexer_by_name(info)
            except pygments.util.ClassNotFound:
                return MarkdownLexer()
        else:
            return MarkdownLexer()

    def print_markdown(self, text, lexer):
        from pygments import highlight
        from pygments.formatters import Terminal256Formatter

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

    def _create_custom_ast_parser(self):
        """Create and configure a custom AST parser with fixed rendering."""
        import mistune

        ast = mistune.create_markdown(renderer="ast")

        # Define the custom render function
        def _iter_render(tokens, state):
            """Fix to a bug where some characters get serialised:
            Test:
                ⋊  python -c 'from hermes.utils.markdown_highlighter import MarkdownHighlighter;
                print(MarkdownHighlighter().process_markdown("`<>!@#$%^&*()-=`"))'
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

        # Apply the custom render function
        ast._iter_render = _iter_render
        return ast

    def _process_parsed_elements(self, parsed_elements):
        """Process parsed markdown elements and render them."""
        output_text = ""
        for element in parsed_elements:
            rendered = self.render_to_markdown(element)
            self.print_markdown(rendered, self.get_lexer(element))
            output_text += rendered
        return output_text

    def _handle_remaining_buffer(self, buffer, ast):
        """Process any remaining content in the buffer."""
        if not buffer:
            return ""

        parsed = ast(buffer)
        return self._process_parsed_elements(parsed)

    def _process_line(self, line, buffer, old_parsed, original_text, output_text, ast):
        """Process a single line of markdown input and update state."""
        original_text += line
        buffer += line

        # Parse current buffer
        parsed = ast(buffer)

        # Skip processing if not valid parsing
        if not isinstance(parsed, list):
            return buffer, old_parsed, original_text, output_text, parsed

        # Skip processing if no new elements
        if len(parsed) == len(old_parsed):
            return buffer, old_parsed, original_text, output_text, parsed

        # Process new elements
        old_parsed = parsed
        buffer = line

        return buffer, old_parsed, original_text, output_text, parsed

    def _process_complete_elements(self, parsed, output_text):
        """Process all complete elements in parsed list."""
        while len(parsed) > 1:
            element = parsed.pop(0)
            rendered = self.render_to_markdown(element)
            self.print_markdown(rendered, self.get_lexer(element))
            output_text += rendered
        return output_text

    def process_markdown(self, markdown_generator: Generator[str, None, None]):
        """Process markdown content and apply syntax highlighting."""
        # Create the AST parser
        ast = self._create_custom_ast_parser()

        # Initialize tracking variables
        buffer = ""
        old_parsed = []
        original_text = ""
        output_text = ""

        # Process each line of input
        for line in self.line_aggregator(markdown_generator):
            buffer, old_parsed, original_text, output_text, parsed = self._process_line(
                line,
                buffer,
                old_parsed,
                original_text,
                output_text,
                ast,
            )

            # Skip to next line if we didn't get valid parsing results
            if not isinstance(parsed, list):
                continue

            # Process all complete elements
            output_text = self._process_complete_elements(parsed, output_text)

        # Process any remaining content
        if buffer:
            output_text += self._handle_remaining_buffer(buffer, ast)

        return original_text
