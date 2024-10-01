import unittest
from unittest.mock import Mock, patch
import base64
from hermes.prompt_builders.claude_prompt_builder import ClaudePromptBuilder
from hermes.file_processors.base import FileProcessor

class TestClaudePromptBuilder(unittest.TestCase):
    def setUp(self):
        self.file_processor = Mock(spec=FileProcessor)
        self.prompt_builder = ClaudePromptBuilder(self.file_processor)

    def test_add_text(self):
        self.prompt_builder.add_text("Hello, world!")
        prompt = self.prompt_builder.build_prompt()
        self.assertEqual(prompt[0], {"type": "text", "text": "Hello, world!"})

    def test_add_text_with_name(self):
        self.prompt_builder.add_text("Hello, world!", name="greeting")
        prompt = self.prompt_builder.build_prompt()
        self.assertEqual(prompt[0], {"type": "text", "text": "greeting:\nHello, world!"})

    def test_add_file(self):
        self.file_processor.read_file.return_value = "File content"
        self.prompt_builder.add_file("test.txt", "test_file")
        prompt = self.prompt_builder.build_prompt()
        self.assertEqual(prompt[0], {"type": "text", "text": "test_file:\nFile content"})

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'image data')
    def test_add_image(self, mock_open):
        self.prompt_builder.add_image("test.png", "test_image")
        prompt = self.prompt_builder.build_prompt()
        self.assertEqual(prompt[0]['type'], 'image')
        self.assertEqual(prompt[0]['source']['type'], 'base64')
        self.assertEqual(prompt[0]['source']['media_type'], 'image/png')
        self.assertEqual(prompt[0]['source']['data'], base64.b64encode(b'image data').decode('utf-8'))

    def test_build_prompt(self):
        self.prompt_builder.add_text("Hello")
        self.prompt_builder.add_text("World", name="greeting")
        prompt = self.prompt_builder.build_prompt()
        self.assertEqual(len(prompt), 2)
        self.assertEqual(prompt[0], {"type": "text", "text": "Hello"})
        self.assertEqual(prompt[1], {"type": "text", "text": "greeting:\nWorld"})

    def test_erase(self):
        self.prompt_builder.add_text("Hello")
        self.prompt_builder.erase()
        prompt = self.prompt_builder.build_prompt()
        self.assertEqual(prompt, [])

if __name__ == '__main__':
    unittest.main()
