import unittest
from unittest.mock import MagicMock, patch, call
from hermes.chat_application import ChatApplication
from tenacity import RetryError


class TestChatApplication(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.ui = MagicMock()
        self.file_processor = MagicMock()
        self.prompt_builder_class = MagicMock()
        self.context_provider_classes = []
        self.hermes_config = MagicMock()
        self.app = ChatApplication(
            self.model,
            self.ui,
            self.file_processor,
            self.prompt_builder_class,
            self.context_provider_classes,
            self.hermes_config
        )
        self.app.history_builder = MagicMock()

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_initial_prompt(self, mock_stdout_isatty, mock_stdin_isatty):
        initial_prompt = "Initial prompt"
        self.ui.get_user_input.side_effect = ["exit"]
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run(initial_prompt)

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", initial_prompt),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.model.send_history.assert_called_once()
        self.ui.display_response.assert_called_once_with("Assistant response")

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_user_input(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["User input", "exit"]
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run()

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", "User input"),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.model.send_history.call_count, 1)
        self.assertEqual(self.ui.display_response.call_count, 1)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('hermes.utils.file_utils.write_file')
    def test_run_with_special_command_append(self, mock_write_file, mock_stdout_isatty, mock_stdin_isatty):
        append_provider = MagicMock()
        append_provider.file_path = 'output.txt'
        self.app.context_providers = [append_provider]
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run(initial_prompt="Test")

        self.model.send_history.assert_called_once()
        self.ui.display_response.assert_called_once_with("Assistant response")
        mock_write_file.assert_called_once_with('output.txt', "\nAssistant response", mode='a')
        expected_calls = [
            call("user", "Test"),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.ui.display_status.assert_called_with("Content appended to output.txt")

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('hermes.utils.file_utils.write_file')
    def test_run_with_special_command_update(self, mock_write_file, mock_stdout_isatty, mock_stdin_isatty):
        update_provider = MagicMock()
        update_provider.file_path = 'output.txt'
        self.app.context_providers = [update_provider]
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run(initial_prompt="Test")

        self.model.send_history.assert_called_once()
        self.ui.display_response.assert_called_once_with("Assistant response")
        mock_write_file.assert_called_once_with('output.txt', 'Assistant response', mode='w')
        expected_calls = [
            call("user", "Test"),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.ui.display_status.assert_called_with("File output.txt updated")

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_keyboard_interrupt(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = KeyboardInterrupt()
        with patch('builtins.print') as mock_print:
            self.app.run()
            mock_print.assert_called_with("\nChat interrupted. Exiting gracefully...")
        self.model.initialize.assert_called_once()

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_multiple_inputs(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["First input", "Second input", "exit"]
        self.model.send_history.side_effect = ["Assistant response 1", "Assistant response 2"]
        self.ui.display_response.side_effect = ["Assistant response 1", "Assistant response 2"]

        self.app.run()

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", "First input"),
            call("assistant", "Assistant response 1"),
            call("user", "Second input"),
            call("assistant", "Assistant response 2")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.model.send_history.call_count, 2)
        self.assertEqual(self.ui.display_response.call_count, 2)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stdout.isatty', return_value=True)
    def test_run_with_quit_command(self, mock_stdout_isatty, mock_stdin_isatty):
        self.ui.get_user_input.side_effect = ["First input", "quit"]
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run()

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", "First input"),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.model.send_history.call_count, 1)
        self.assertEqual(self.ui.display_response.call_count, 1)

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdin.read', return_value="Piped input")
    def test_run_with_piped_input(self, mock_stdin_read, mock_stdout_isatty, mock_stdin_isatty):
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run()

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", "Piped input"),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.model.send_history.assert_called_once()
        self.ui.display_response.assert_called_once_with("Assistant response")

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdout.isatty', return_value=True)
    @patch('sys.stdin.read', return_value="Piped input")
    def test_run_with_piped_input_and_initial_prompt(self, mock_stdin_read, mock_stdout_isatty, mock_stdin_isatty):
        initial_prompt = "Initial prompt"
        self.model.send_history.side_effect = ["Assistant response 1", "Assistant response 2"]
        self.ui.display_response.side_effect = ["Assistant response 1", "Assistant response 2"]

        self.app.run(initial_prompt=initial_prompt)

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", initial_prompt),
            call("assistant", "Assistant response 1"),
            call("user", "Piped input"),
            call("assistant", "Assistant response 2")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.model.send_history.assert_called_twice()
        self.ui.display_response.assert_has_calls([
            call("Assistant response 1"),
            call("Assistant response 2")
        ], any_order=False)

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdout.isatty', return_value=False)
    @patch('sys.stdin.read', return_value="Piped input")
    def test_run_with_piped_input_and_output(self, mock_stdin_read, mock_stdout_isatty, mock_stdin_isatty):
        initial_prompt = "Initial prompt"
        self.model.send_history.return_value = "Assistant response"
        self.ui.display_response.return_value = "Assistant response"

        self.app.run(initial_prompt=initial_prompt)

        self.model.initialize.assert_called_once()
        expected_calls = [
            call("user", initial_prompt),
            call("assistant", "Assistant response")
        ]
        self.app.history_builder.add_message.assert_has_calls(expected_calls, any_order=False)
        self.model.send_history.assert_called_once()
        self.ui.display_response.assert_called_once_with("Assistant response")

    @patch('hermes.chat_application.retry')
    def test_send_model_request_with_retry(self, mock_retry):
        mock_retry.return_value = lambda f: f
        self.model.send_history.side_effect = [Exception("API Error"), "Success"]
        self.ui.display_response.return_value = "Success"

        with self.assertLogs(level='ERROR') as log:
            result = self.app.send_message_and_print_output("Test input")

        self.assertEqual(result, "Success")
        self.model.send_history.assert_called()
        self.ui.display_response.assert_called_with("Success")
        self.app.history_builder.add_message.assert_has_calls([
            call("user", "Test input"),
            call("assistant", "Success")
        ])
        self.assertIn("Error during model request: API Error", log.output[0])

    @patch('hermes.chat_application.retry')
    def test_send_model_request_success_after_retry(self, mock_retry):
        mock_retry.return_value = lambda f: f
        self.model.send_history.side_effect = [Exception("API Error"), "Success"]
        self.ui.display_response.return_value = "Success"

        result = self.app.send_message_and_print_output("Test input")

        self.assertEqual(result, "Success")
        self.model.send_history.assert_called()
        self.ui.display_response.assert_called_with("Success")
        self.app.history_builder.add_message.assert_has_calls([
            call("user", "Test input"),
            call("assistant", "Success")
        ])


if __name__ == '__main__':
    unittest.main()
