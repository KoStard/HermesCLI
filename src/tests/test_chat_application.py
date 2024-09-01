import unittest
from unittest.mock import MagicMock, patch
from hermes.chat_application import ChatApplication

class TestChatApplication(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.ui = MagicMock()
        self.file_processor = MagicMock()
        self.prompt_formatter = MagicMock()
        self.special_command_prompts = MagicMock()
        self.app = ChatApplication(self.model, self.ui, self.file_processor, self.prompt_formatter, self.special_command_prompts)

    def test_set_files(self):
        files = {'file1': 'path/to/file1', 'file2': 'path/to/file2'}
        self.app.set_files(files)
        self.assertEqual(self.app.files, files)

    def test_run_with_initial_prompt(self):
        initial_prompt = "Initial prompt"
        self.ui.get_user_input.side_effect = ["exit"]
        self.app.run(initial_prompt)
        self.model.initialize.assert_called_once()
        self.prompt_formatter.format_prompt.assert_called_once_with(self.app.files, initial_prompt, None)
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()

    def test_run_with_user_input(self):
        self.ui.get_user_input.side_effect = ["User input", "exit"]
        self.app.run()
        self.model.initialize.assert_called_once()
        self.assertEqual(self.model.send_message.call_count, 1)
        self.assertEqual(self.ui.display_response.call_count, 1)

    def test_run_with_special_command_append(self):
        special_command = {'append': 'output.txt'}
        self.ui.display_response.return_value = "Response content"
        self.app.files = {'output.txt': 'path/to/output.txt'}  # Set up the files dictionary
        self.app.run(initial_prompt="Test", special_command=special_command)
        self.file_processor.write_file.assert_called_once_with('path/to/output.txt', "\nResponse content", mode='a')
        self.ui.display_status.assert_called_once_with("Content appended to output.txt")

    def test_run_with_special_command_update(self):
        special_command = {'update': 'output.txt'}
        self.ui.display_response.return_value = "Response content"
        self.app.files = {'output.txt': 'path/to/output.txt'}  # Set up the files dictionary
        self.app.run(initial_prompt="Test", special_command=special_command)
        self.file_processor.write_file.assert_called_once_with('path/to/output.txt', "Response content", mode='w')
        self.ui.display_status.assert_called_once_with("File output.txt updated")

    def test_run_with_keyboard_interrupt(self):
        self.ui.get_user_input.side_effect = KeyboardInterrupt()
        with patch('builtins.print') as mock_print:
            self.app.run()
            mock_print.assert_called_with("\nChat interrupted. Exiting gracefully...")

    def test_run_with_multiple_inputs(self):
        self.ui.get_user_input.side_effect = ["First input", "Second input", "exit"]
        self.app.run()
        self.model.initialize.assert_called_once()
        self.assertEqual(self.model.send_message.call_count, 2)
        self.assertEqual(self.ui.display_response.call_count, 2)

    def test_run_with_quit_command(self):
        self.ui.get_user_input.side_effect = ["First input", "quit"]
        self.app.run()
        self.model.initialize.assert_called_once()
        self.assertEqual(self.model.send_message.call_count, 1)
        self.assertEqual(self.ui.display_response.call_count, 1)

if __name__ == '__main__':
    unittest.main()
