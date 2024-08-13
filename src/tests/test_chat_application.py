import unittest
from unittest.mock import MagicMock, patch
from hermes.chat_application import ChatApplication

class TestChatApplication(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.ui = MagicMock()
        self.file_processor = MagicMock()
        self.prompt_formatter = MagicMock()
        self.app = ChatApplication(self.model, self.ui, self.file_processor, self.prompt_formatter)

    def test_run_with_special_command(self):
        initial_content = "Initial content"
        special_command = {'append': 'test.txt'}
        self.model.send_message.return_value = "Response"
        self.ui.display_response.return_value = "Formatted response"

        self.app.run(initial_content, special_command)

        self.model.initialize.assert_called_once()
        self.model.send_message.assert_called_once_with(initial_content)
        self.ui.display_response.assert_called_once()
        self.file_processor.write_file.assert_called_once_with('test.txt', "\nFormatted response", mode='a')

    @patch('builtins.input', side_effect=['Test input', 'exit'])
    def test_run_without_special_command(self, mock_input):
        initial_content = "Initial content"
        self.model.send_message.return_value = "Response"
        self.ui.display_response.return_value = "Formatted response"
        self.prompt_formatter.add_content.return_value = "Updated content"

        self.app.run(initial_content)

        self.model.initialize.assert_called()
        self.model.send_message.assert_called_with("Updated content")
        self.ui.display_response.assert_called()
        self.ui.get_user_input.assert_called()

    def test_append_to_file(self):
        self.app.append_to_file('test.txt', 'Content to append')
        self.file_processor.write_file.assert_called_once_with('test.txt', "\nContent to append", mode='a')
        self.ui.display_status.assert_called_once_with("Content appended to test.txt")

    def test_update_file(self):
        self.app.update_file('test.txt', 'New content')
        self.file_processor.write_file.assert_called_once_with('test.txt', 'New content', mode='w')
        self.ui.display_status.assert_called_once_with("File test.txt updated")

if __name__ == '__main__':
    unittest.main()
