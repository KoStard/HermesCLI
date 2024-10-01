import unittest
from unittest.mock import Mock, patch
from io import StringIO
from hermes.chat_ui import ChatUI
from hermes.utils.markdown_highlighter import MarkdownHighlighter

class TestChatUI(unittest.TestCase):
    def setUp(self):
        self.markdown_highlighter = Mock(spec=MarkdownHighlighter)
        self.chat_ui = ChatUI(print_pretty=False, use_highlighting=False, markdown_highlighter=self.markdown_highlighter)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_raw_response(self, mock_stdout):
        response_generator = (word for word in ["Hello", " ", "world"])
        result = self.chat_ui._display_raw_response(response_generator)
        self.assertEqual(result, "Hello world")
        self.assertEqual(mock_stdout.getvalue(), "Hello world\n")

    def test_display_highlighted_response(self):
        self.markdown_highlighter.process_markdown.return_value = "# Hello world"

        response_generator = (word for word in ["# Hello", " ", "world"])
        result = self.chat_ui._display_highlighted_response(response_generator)

        self.assertEqual(result, "# Hello world")
        self.markdown_highlighter.process_markdown.assert_called_once()

    @patch('builtins.input', return_value="Hello")
    @patch('os.isatty', return_value=True)
    def test_get_user_input_terminal(self, mock_isatty, mock_input):
        result = self.chat_ui.get_user_input()
        self.assertEqual(result, "Hello")

    @patch('sys.stdin.read', return_value="Hello from pipe")
    @patch('os.isatty', return_value=False)
    def test_get_user_input_pipe(self, mock_isatty, mock_stdin_read):
        result = self.chat_ui.get_user_input()
        self.assertEqual(result, "Hello from pipe")

    @patch('rich.console.Console.print')
    def test_display_status(self, mock_print):
        self.chat_ui.display_status("Test status")
        mock_print.assert_called_once()

if __name__ == '__main__':
    unittest.main()
