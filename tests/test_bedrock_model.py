import unittest
from unittest.mock import Mock, patch
from hermes.chat_models.bedrock import BedrockModel

class TestBedrockModel(unittest.TestCase):
    def setUp(self):
        self.config = {
            "model_identifier": "bedrock/sonnet-3",
            "aws_region": "us-east-1"
        }
        self.model = BedrockModel(self.config, "bedrock")

    @patch('boto3.client')
    def test_initialize(self, mock_boto3_client):
        self.model.initialize()
        mock_boto3_client.assert_called_once_with('bedrock-runtime', region_name='us-east-1')
        self.assertEqual(self.model.model_id, 'anthropic.claude-3-sonnet-20240229-v1:0')

    @patch('boto3.client')
    def test_send_history(self, mock_boto3_client):
        mock_client = Mock()
        mock_client.converse_stream.return_value = {
            'stream': [
                {'contentBlockDelta': {'delta': {'text': 'Hello'}}},
                {'contentBlockDelta': {'delta': {'text': ' world'}}},
                {'messageStop': {}}
            ]
        }
        mock_boto3_client.return_value = mock_client

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        result = list(self.model.send_history(messages))

        self.assertEqual(result, ["Hello", " world"])
        mock_client.converse_stream.assert_called_once_with(
            modelId=self.model.model_id,
            messages=messages
        )

if __name__ == '__main__':
    unittest.main()
