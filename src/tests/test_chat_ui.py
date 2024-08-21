import unittest
from unittest.mock import MagicMock, patch
from io import StringIO
from hermes.ui.chat_ui import ChatUI

class TestChatUI(unittest.TestCase):
    def setUp(self):
        self.chat_ui = ChatUI(prints_raw=False)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_response_raw(self, mock_stdout):
        chat_ui = ChatUI(prints_raw=True)
        response_generator = (word for word in ["Hello", " ", "world"])
        result = chat_ui.display_response(response_generator)
        self.assertEqual(result, "Hello world")
        self.assertEqual(mock_stdout.getvalue(), "Hello world\n")

    @patch('rich.live.Live')
    def test_display_response_formatted(self, mock_live):
        response_generator = (word for word in ["Hello", " ", "world"])
        result = self.chat_ui.display_response(response_generator)
        self.assertEqual(result, "Hello world")
        mock_live.return_value.__enter__.return_value.update.assert_called()

    @patch('builtins.input', side_effect=["", "  ", "Hello"])
    def test_get_user_input(self, mock_input):
        result = self.chat_ui.get_user_input()
        self.assertEqual(result, "Hello")
        self.assertEqual(mock_input.call_count, 3)

    @patch('rich.console.Console.print')
    def test_display_status(self, mock_print):
        self.chat_ui.display_status("Test message")
        mock_print.assert_called_once_with("Test message")

if __name__ == '__main__':
    unittest.main()
