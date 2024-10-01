import unittest
from unittest.mock import Mock, patch
from hermes.chat_models.vertex import VertexModel
import openai

class TestVertexModel(unittest.TestCase):
    def setUp(self):
        self.config = {
            "project_id": "test-project",
            "VERTEX": {}
        }
        self.model = VertexModel(self.config, "vertex")

    def test_initialize(self):
        mock_credentials = Mock()
        mock_auth_request = Mock()
        mock_openai_client = Mock()

        self.model.initialize(mock_credentials, mock_auth_request, mock_openai_client)

        mock_credentials.refresh.assert_called_once_with(mock_auth_request)
        mock_openai_client.assert_called_once()
        self.assertEqual(self.model.model_id, "meta/llama3-405b-instruct-maas")

    @patch('openai.OpenAI')
    def test_send_history(self, mock_openai):
        mock_stream = Mock()
        mock_stream.__iter__.return_value = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" world"))]),
        ]
        mock_openai.return_value.chat.completions.create.return_value = mock_stream

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        result = list(self.model.send_history(messages))

        self.assertEqual(result, ["Hello", " world"])
        mock_openai.return_value.chat.completions.create.assert_called_once_with(
            model=self.model.model_id,
            messages=messages,
            stream=True
        )

    @patch('openai.OpenAI')
    def test_send_history_authentication_error(self, mock_openai):
        mock_openai.return_value.chat.completions.create.side_effect = openai.AuthenticationError("Auth failed")

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        with self.assertRaises(Exception) as context:
            list(self.model.send_history(messages))

        self.assertIn("Authentication failed", str(context.exception))

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import Mock, patch
from hermes.chat_models.vertex import VertexModel
import openai

class TestVertexModel(unittest.TestCase):
    def setUp(self):
        self.config = {
            "project_id": "test-project",
            "VERTEX": {}
        }
        self.model = VertexModel(self.config, "vertex")

    @patch('google.auth.default')
    @patch('google.auth.transport.requests.Request')
    def test_initialize(self, mock_auth_request, mock_auth_default):
        mock_auth_default.return_value = (Mock(), Mock())
        self.model.initialize()

        self.assertEqual(self.model.model_id, "meta/llama3-405b-instruct-maas")

    @patch('google.auth.transport.requests.Request')
    @patch('google.auth.default')
    @patch('openai.OpenAI')
    def test_send_history(self, mock_openai, mock_auth_default, mock_auth_request):
        mock_auth_default.return_value = (Mock(), Mock())
        mock_results = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" world"))]),
        ]
        mock_openai.return_value.chat.completions.create.return_value = mock_results

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        result = list(self.model.send_history(messages))

        self.assertEqual(result, ["Hello", " world"])
        mock_openai.return_value.chat.completions.create.assert_called_once_with(
            model=self.model.model_id,
            messages=messages,
            stream=True
        )

    @patch('google.auth.transport.requests.Request')
    @patch('google.auth.default')
    @patch('openai.OpenAI')
    def test_send_history_authentication_error(self, mock_openai, mock_auth_default, mock_auth_request):
        mock_auth_default.return_value = (Mock(), Mock())
        mock_openai.return_value.chat.completions.create.side_effect = openai.AuthenticationError("Auth failed", response=Mock(status_code=401), body=None)

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        with self.assertRaises(Exception) as context:
            list(self.model.send_history(messages))

        self.assertIn("Authentication failed", str(context.exception))

if __name__ == '__main__':
    unittest.main()
