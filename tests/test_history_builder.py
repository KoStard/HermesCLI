import unittest
from unittest.mock import Mock, patch
from hermes.history_builder import HistoryBuilder
from hermes.prompt_builders.base import PromptBuilder
from hermes.file_processors.base import FileProcessor
from hermes.context_providers.base import ContextProvider

class TestHistoryBuilder(unittest.TestCase):
    def setUp(self):
        self.prompt_builder_class = Mock(spec=PromptBuilder)
        self.file_processor = Mock(spec=FileProcessor)
        self.history_builder = HistoryBuilder(self.prompt_builder_class, self.file_processor)

    def test_add_assistant_reply(self):
        self.history_builder.add_assistant_reply("Hello")
        self.assertEqual(len(self.history_builder.chunks), 1)
        self.assertEqual(self.history_builder.chunks[0], {"author": "assistant", "text": "Hello"})

    def test_add_user_input(self):
        self.history_builder.add_user_input("Hi", active=True)
        self.assertEqual(len(self.history_builder.chunks), 1)
        self.assertEqual(self.history_builder.chunks[0], {"author": "user", "text": "Hi", "active": True, "permanent": False})

    def test_add_context(self):
        mock_context_provider = Mock(spec=ContextProvider)
        self.history_builder.add_context(mock_context_provider, active=True)
        self.assertEqual(len(self.history_builder.chunks), 1)
        self.assertEqual(self.history_builder.chunks[0]["author"], "user")
        self.assertEqual(self.history_builder.chunks[0]["context_provider"], mock_context_provider)
        self.assertTrue(self.history_builder.chunks[0]["active"])

    def test_build_messages(self):
        self.history_builder.add_assistant_reply("Hello")
        self.history_builder.add_user_input("Hi", active=True)
        
        messages = self.history_builder.build_messages()
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "assistant")
        self.assertEqual(messages[1]["role"], "user")

    def test_clear_regular_history(self):
        self.history_builder.add_assistant_reply("Hello")
        self.history_builder.add_user_input("Hi", active=True)
        self.history_builder.add_user_input("Permanent", active=True, permanent=True)
        
        self.history_builder.clear_regular_history()
        
        self.assertEqual(len(self.history_builder.chunks), 1)
        self.assertEqual(self.history_builder.chunks[0]["text"], "Permanent")

    def test_run_pending_actions(self):
        mock_context_provider = Mock(spec=ContextProvider)
        mock_context_provider.is_action.return_value = True
        mock_context_provider.perform_action.return_value = "Action performed"
        mock_ui = Mock()

        self.history_builder.add_context(mock_context_provider, active=True)
        self.history_builder.add_assistant_reply("Response")

        self.history_builder.run_pending_actions(lambda x: x.perform_action(None), mock_ui)

        mock_context_provider.perform_action.assert_called_once()
        mock_ui.display_status.assert_called_once_with("Action performed")

    def test_get_recent_llm_response(self):
        self.history_builder.add_user_input("Hello")
        self.history_builder.add_assistant_reply("Hi there")
        self.history_builder.add_user_input("How are you?")
        self.history_builder.add_assistant_reply("I'm doing well, thanks!")

        recent_response = self.history_builder.get_recent_llm_response()
        self.assertEqual(recent_response, "I'm doing well, thanks!")

if __name__ == '__main__':
    unittest.main()
