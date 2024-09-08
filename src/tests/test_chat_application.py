import unittest
from unittest.mock import MagicMock, patch, call
from hermes.chat_application import ChatApplication

class TestChatApplication(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.ui = MagicMock()
        self.prompt_builder = MagicMock()
        self.special_command_prompts = MagicMock()
        self.context_orchestrator = MagicMock()
        self.app = ChatApplication(self.model, self.ui, self.prompt_builder, self.special_command_prompts, self.context_orchestrator)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_initial_prompt(self, mock_stdout_isatty, mock_stdin_isatty):
        initial_prompt = "Initial prompt"
        self.ui.get_user_input.side_effect = ["exit"]
        self.app.run(initial_prompt)
        self.model.initialize.assert_called_once()
        self.context_orchestrator.add_to_prompt.assert_called_once_with(self.prompt_builder)
        self.prompt_builder.add_text.assert_called_once_with(initial_prompt)
        self.prompt_builder.build_prompt.assert_called_once()
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_user_input(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["User input", "exit"]
        self.app.run()
        self.model.initialize.assert_called_once()
        self.assertEqual(self.model.send_message.call_count, 1)
        self.assertEqual(self.ui.display_response.call_count, 1)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('hermes.utils.file_utils.write_file')
    def test_run_with_special_command_append(self, mock_write_file, mock_stdout_isatty, mock_stdin_isatty):
        special_command = {'append': 'output.txt'}
        self.ui.display_response.return_value = "Response content"
        self.app.run(initial_prompt="Test", special_command=special_command)
        self.prompt_builder.add_text.assert_has_calls([
            call("Test"),
            call(self.special_command_prompts['append'].format(file_name='output.txt'))
        ])
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()
        mock_write_file.assert_called_once_with('output.txt', '\nResponse content', mode='a')
    
    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('hermes.utils.file_utils.write_file')
    def test_run_with_special_command_update(self, mock_write_file, mock_stdout_isatty, mock_stdin_isatty):
        special_command = {'update': 'output.txt'}
        self.ui.display_response.return_value = "Response content"
        self.app.run(initial_prompt="Test", special_command=special_command)
        self.prompt_builder.add_text.assert_has_calls([
            call("Test"),
            call(self.special_command_prompts['update'].format(file_name='output.txt'))
        ])
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()
        mock_write_file.assert_called_once_with('output.txt', 'Response content', mode='w')

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_keyboard_interrupt(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = KeyboardInterrupt()
        with patch('builtins.print') as mock_print:
            self.app.run()
            mock_print.assert_called_with("\nChat interrupted. Exiting gracefully...")

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_multiple_inputs(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["First input", "Second input", "exit"]
        self.app.run()
        self.model.initialize.assert_called_once()
        self.assertEqual(self.model.send_message.call_count, 2)
        self.assertEqual(self.ui.display_response.call_count, 2)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_quit_command(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["First input", "quit"]
        self.app.run()
        self.model.initialize.assert_called_once()
        self.assertEqual(self.model.send_message.call_count, 1)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_clear_command(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["/clear", "User input", "exit"]
        self.app.run()
        self.model.initialize.assert_called()
        self.assertEqual(self.model.initialize.call_count, 2)  # Once at start, once after /clear
        self.ui.display_status.assert_called_with("Chat history cleared.")
        self.assertEqual(self.model.send_message.call_count, 1)

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdin.read')
    def test_run_with_piped_input(self, mock_stdin_read, mock_stdout_isatty, mock_stdin_isatty):
        mock_stdin_read.return_value = "Piped input"
        self.app.run()
        self.model.initialize.assert_called_once()
        self.context_orchestrator.add_to_prompt.assert_called_once_with(self.prompt_builder)
        self.prompt_builder.add_text.assert_called_once_with("Piped input")
        self.prompt_builder.build_prompt.assert_called_once()
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdin.read')
    def test_run_with_piped_input_and_initial_prompt(self, mock_stdin_read, mock_stdout_isatty, mock_stdin_isatty):
        mock_stdin_read.return_value = "Piped input"
        self.app.run(initial_prompt="Initial prompt")
        self.model.initialize.assert_called_once()
        self.context_orchestrator.add_to_prompt.assert_called_once_with(self.prompt_builder)
        self.prompt_builder.add_text.assert_has_calls([call('Initial prompt'), call('Piped input')])
        self.prompt_builder.build_prompt.assert_called_once()
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdout.isatty', return_value=False)
    @patch('sys.stdin.read')
    def test_run_with_piped_input_and_output(self, mock_stdin_read, mock_stdout_isatty, mock_stdin_isatty):
        mock_stdin_read.return_value = "Piped input"
        self.app.run(initial_prompt="Initial prompt")
        self.model.initialize.assert_called_once()
        self.context_orchestrator.add_to_prompt.assert_called_once_with(self.prompt_builder)
        self.prompt_builder.add_text.assert_has_calls([call('Initial prompt'), call('Piped input')])
        self.prompt_builder.build_prompt.assert_called_once()
        self.model.send_message.assert_called_once()
        self.ui.display_response.assert_called_once()

if __name__ == '__main__':
    unittest.main()
