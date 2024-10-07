import argparse
import sys
import unittest
from unittest.mock import Mock, patch
from hermes.chat_application import ChatApplication
from hermes.chat_models.base import ChatModel
from hermes.chat_ui import ChatUI
from hermes.context_providers.prompt_context_provider import PromptContextProvider
from hermes.history_builder import HistoryBuilder
from hermes.context_providers.base import ContextProvider
class TestChatApplication(unittest.TestCase):
    def setUp(self):
        self.model = Mock(spec=ChatModel)
        self.ui = Mock(spec=ChatUI)
        self.history_builder = Mock(spec=HistoryBuilder)
        self.mock_context_provider = Mock(spec=ContextProvider, get_command_key=Mock(return_value="key1"))
        self.mock_context_provider_instance = Mock(spec=ContextProvider)
        self.mock_context_provider.return_value = self.mock_context_provider_instance
        self.mock_context_provider_instance.get_required_providers.return_value = {}
        self.mock_context_provider_instance.load_context_from_cli.return_value = None
        self.mock_context_provider_instance.load_context_from_string.return_value = None
        self.mock_context_provider_instance.counts_as_input.return_value = False

        self.mock_prompt_context_provider = Mock(spec=PromptContextProvider, counts_as_input=Mock(return_value=True))

        self.command_keys_map = {"key1": self.mock_context_provider}
        self.args = Mock(spec=argparse.Namespace)
        self.args.key1 = "value1"
        self.args.load_history = None

        self.chat_app = ChatApplication(
            self.model,
            self.ui,
            self.history_builder,
            self.command_keys_map,
            self.args
        )

    def test_initialisation(self):
        self.assertIsInstance(self.chat_app, ChatApplication)
        self.assertEqual(self.chat_app.model, self.model)
        self.assertEqual(self.chat_app.ui, self.ui)
        self.assertEqual(self.chat_app.history_builder, self.history_builder)
        self.assertEqual(self.chat_app.command_keys_map, {"key1": self.mock_context_provider})

    def test_user_round(self):
        self.history_builder.requires_user_input.side_effect = [True, False]
        self.chat_app.get_user_input = Mock(return_value="test input")

        result = self.chat_app.user_round()

        self.assertIsNone(result)
        self.chat_app.get_user_input.assert_called_once()

    def test_user_round_with_exit(self):
        self.history_builder.requires_user_input.side_effect = [True, False]
        self.chat_app.get_user_input = Mock(return_value="exit")

        result = self.chat_app.user_round()
        self.assertEqual(result, "exit")
    
    def test_user_round_with_keyboard_interrupt(self):
        self.history_builder.requires_user_input.side_effect = [True, False]
        self.chat_app.get_user_input = Mock(side_effect=KeyboardInterrupt)

        result = self.chat_app.user_round()
        self.assertIsNone(result)

    def test_user_round_with_keyboard_interrupt_twice(self):
        self.history_builder.requires_user_input.side_effect = [True, True]
        self.chat_app.get_user_input = Mock(side_effect=KeyboardInterrupt)

        result = self.chat_app.user_round()
        self.assertEqual(result, "exit")

    def test_run_chat(self):
        self.chat_app.user_round = Mock(return_value='')
        self.chat_app.llm_round = Mock()
        self.chat_app.decide_to_continue = Mock(return_value=False)

        self.chat_app.run_chat(run_once=False)

        self.chat_app.user_round.assert_called_once()
        self.chat_app.llm_round.assert_called_once()
        self.chat_app.decide_to_continue.assert_called_once()
    
    def test_run_chat_with_exit(self):
        self.chat_app.user_round = Mock(return_value='exit')
        self.chat_app.llm_round = Mock()
        self.chat_app.decide_to_continue = Mock(return_value=False)

        self.chat_app.run_chat(run_once=False)

    def test_llm_interact(self):
        self.chat_app.history_builder.build_messages = Mock(return_value=["message1", "message2"])
        self.chat_app._send_model_request = Mock(return_value="response")
        self.chat_app.ui.display_response = Mock(return_value="response")
        self.chat_app._llm_interact()
        self.chat_app.history_builder.add_assistant_reply.assert_called_once_with("response")
    
    def test_llm_interact_with_error(self):
        self.chat_app.history_builder.build_messages = Mock(return_value=["message1", "message2"])
        self.chat_app._send_model_request = Mock(side_effect=Exception("Test exception"))
        self.chat_app.ui.display_response = Mock(return_value="response")

        with self.assertRaises(Exception):
            self.chat_app._llm_interact()
    
    def test_llm_interact_with_keyboard_interrupt(self):
        self.chat_app.history_builder.build_messages = Mock(return_value=["message1", "message2"])
        self.chat_app._send_model_request = Mock(side_effect=KeyboardInterrupt)
        self.chat_app.ui.display_response = Mock(return_value="response")
        self.chat_app._llm_interact()
        self.chat_app.history_builder.force_need_for_user_input.assert_called_once()

    def test_llm_act(self):
        self.chat_app.history_builder.get_recent_llm_response = Mock(return_value="response")
        self.chat_app.history_builder.run_pending_actions = Mock()
        self.chat_app._llm_act()
        self.chat_app.history_builder.run_pending_actions.assert_called_once()

    def test_decide_to_continue(self):
        sys.stdout.isatty = Mock(return_value=True)
        self.assertTrue(self.chat_app.decide_to_continue(run_once=False))


    def test_get_user_input(self):
        self.chat_app.ui.get_user_input.return_value = "test input"
        self.chat_app._setup_initial_context_provider = Mock(return_value=[
            self.mock_prompt_context_provider
        ])
        self.chat_app.get_user_input()
        self.history_builder.add_context.assert_called_with(self.mock_prompt_context_provider, True, permanent=False)

    def test_get_user_input_with_exit(self):
        self.chat_app.ui.get_user_input.return_value = "/exit"
        response = self.chat_app.get_user_input()
        self.assertEqual(response, "exit")
    
    def test_get_user_input_with_clear(self):
        self.chat_app.ui.get_user_input.side_effect = ["/clear", "test input"]
        self.chat_app.clear_chat = Mock()
        self.chat_app.get_user_input()
        self.chat_app.clear_chat.assert_called_once()
        self.history_builder.add_user_input.assert_not_called()
        prompt_context_provider_mock = Mock(spec=PromptContextProvider, counts_as_input=Mock(return_value=True))
        self.chat_app._setup_initial_context_provider = Mock(return_value=[
            prompt_context_provider_mock
        ])
        self.chat_app.get_user_input()
        self.history_builder.add_context.assert_called_with(prompt_context_provider_mock, True, permanent=False)

    def test_send_model_request(self):
        messages = ["message1", "message2"]
        self.model.send_history = Mock(return_value=iter("response"))
        self.assertEqual(list(self.chat_app._send_model_request(messages)), list("response"))

    def test_clear_chat(self):
        self.chat_app.clear_chat()
        self.history_builder.clear_regular_history.assert_called_once()
        self.ui.display_status.assert_called_once_with("Chat history cleared.")

    def test_llm_round(self):
        self.chat_app._llm_interact = Mock()
        self.chat_app._llm_act = Mock()

        self.chat_app.llm_round()

        self.chat_app._llm_interact.assert_called_once()
        self.chat_app._llm_act.assert_called_once()

if __name__ == '__main__':
    unittest.main()
