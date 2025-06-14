from unittest.mock import Mock, patch

import pytest

from hermes.chat.conversation_orchestrator import ConversationOrchestrator
from hermes.chat.events import MessageEvent
from hermes.chat.history import History
from hermes.chat.messages.text import TextMessage


class TestConversationOrchestrator:
    @pytest.fixture
    def mock_mcp_manager(self):
        manager = Mock()
        manager.initial_load_complete = False
        manager.has_errors.return_value = False
        manager._errors_acknowledged = False
        return manager

    @pytest.fixture
    def mock_notifications_printer(self):
        return Mock()

    @pytest.fixture
    def mock_user_participant(self):
        user = Mock()
        user.get_name.return_value = "user"
        user.get_input_and_run_commands.return_value = []
        return user

    @pytest.fixture
    def mock_assistant_participant(self):
        assistant = Mock()
        assistant.get_name.return_value = "assistant"
        assistant.is_agent_mode_enabled.return_value = False
        assistant.orchestrator = Mock()
        assistant.get_input_and_run_commands.return_value = []
        return assistant

    @pytest.fixture
    def conversation_orchestrator(self, mock_user_participant, mock_assistant_participant, mock_mcp_manager):
        history = History()
        orchestrator = ConversationOrchestrator(
            user_participant=mock_user_participant,
            assistant_participant=mock_assistant_participant,
            history=history,
            mcp_manager=mock_mcp_manager,
        )
        orchestrator.notifications_printer = Mock()
        return orchestrator

    def test_wait_for_mcps_and_update_commands(self, conversation_orchestrator, mock_mcp_manager):
        # Test when MCPs are not yet loaded
        mock_mcp_manager.initial_load_complete = False

        conversation_orchestrator._wait_for_mcps_and_update_commands()

        # Verify wait_for_initial_load was called
        mock_mcp_manager.wait_for_initial_load.assert_called_once()

        # Test when MCPs are already loaded
        mock_mcp_manager.initial_load_complete = True
        mock_mcp_manager.wait_for_initial_load.reset_mock()

        conversation_orchestrator._wait_for_mcps_and_update_commands()

        # Verify wait_for_initial_load was not called again
        mock_mcp_manager.wait_for_initial_load.assert_not_called()

    def test_ensure_mcps_are_checked_before_sending_messages(self, conversation_orchestrator, mock_user_participant):
        # Create a mock event
        message = TextMessage(author="user", text="Hello")
        event = MessageEvent(message)

        # Mock user input to return our event
        mock_user_participant.get_input_and_run_commands.return_value = [event]

        # Patch the _wait_for_mcps_and_update_commands method to check if it's called
        with patch.object(conversation_orchestrator, "_wait_for_mcps_and_update_commands") as mock_wait:
            # Call the method that should ensure MCPs are loaded
            conversation_orchestrator._get_user_input_and_run_commands()
            conversation_orchestrator._consume_events_from_user_and_render_assistant(
                conversation_orchestrator._get_user_input_and_run_commands()
            )

            # Verify that _wait_for_mcps_and_update_commands was called
            mock_wait.assert_called_once()
