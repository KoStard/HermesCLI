import unittest
from unittest.mock import MagicMock, patch
from hermes.prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder
from hermes.file_processors.base import FileProcessor

class TestBedrockPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.mock_file_processor = MagicMock(spec=FileProcessor)
        self.bedrock_prompt_builder = BedrockPromptBuilder(self.mock_file_processor)

    def test_add_text(self):
        self.bedrock_prompt_builder.add_text("Hello, world!")
        self.assertEqual(self.bedrock_prompt_builder.contents, [{'text': 'Hello, world!\n'}])

    def test_add_text_with_name(self):
        self.bedrock_prompt_builder.add_text("Hello, world!", name="greeting")
        self.assertEqual(self.bedrock_prompt_builder.contents, [{'text': 'greeting:\nHello, world!\n'}])

    def test_add_file_binary(self):
        self.mock_file_processor.read_file.return_value = 'binary_content'
        self.bedrock_prompt_builder.add_file('test.pdf', 'test_doc')
        self.assertEqual(self.bedrock_prompt_builder.contents, [{
            'text': '<document name="test_doc">binary_content</document>'
        }])

    def test_add_file_text(self):
        self.mock_file_processor.read_file.return_value = 'text_content'
        self.bedrock_prompt_builder.add_file('test.txt', 'test_doc')
        self.assertEqual(self.bedrock_prompt_builder.contents, [{
            'text': '<document name="test_doc">text_content</document>'
        }])

    def test_add_image(self):
        self.mock_file_processor.read_file.return_value = b'image_content'
        self.bedrock_prompt_builder.add_image('test.jpg', 'test_image')
        self.assertEqual(self.bedrock_prompt_builder.contents, [{
            'image': {
                'format': 'jpg',
                'source': {
                    'bytes': b'image_content'
                }
            }
        }])

    def test_build_prompt(self):
        self.bedrock_prompt_builder.add_text("Hello")
        self.bedrock_prompt_builder.add_text("World")
        self.assertEqual(self.bedrock_prompt_builder.build_prompt(), [
            {'text': 'Hello\n'},
            {'text': 'World\n'}
        ])

if __name__ == '__main__':
    unittest.main()
