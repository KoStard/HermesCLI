import unittest
from hermes.prompt_formatters.xml import XMLPromptFormatter
from hermes.prompt_formatters.bedrock import BedrockPromptFormatter
from hermes.file_processors.default import DefaultFileProcessor
from hermes.file_processors.bedrock import BedrockFileProcessor

class TestXMLPromptFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = XMLPromptFormatter(DefaultFileProcessor())

    def test_format_prompt(self):
        files = {'test_file': 'path/to/test_file.txt'}
        prompt = 'Test prompt'
        result = self.formatter.format_prompt(files, prompt)
        self.assertIn('<input>', result)
        self.assertIn('<systemMessage>', result)
        self.assertIn('<document name="test_file">', result)
        self.assertIn('<prompt>Test prompt</prompt>', result)

    def test_add_content(self):
        current = '<input><prompt>Initial prompt</prompt></input>'
        content_to_add = 'Additional content'
        result = self.formatter.add_content(current, content_to_add)
        self.assertIn('Initial prompt', result)
        self.assertIn('Additional content', result)

class TestBedrockPromptFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = BedrockPromptFormatter(BedrockFileProcessor())

    def test_format_prompt(self):
        files = {'test_file': 'path/to/test_file.txt'}
        prompt = 'Test prompt'
        result = self.formatter.format_prompt(files, prompt)
        self.assertIsInstance(result, list)
        self.assertTrue(any('text' in item for item in result))
        self.assertTrue(any('Test prompt' in item.get('text', '') for item in result))

    def test_add_content(self):
        current = [{'text': 'Initial prompt'}]
        content_to_add = 'Additional content'
        result = self.formatter.add_content(current, content_to_add)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]['text'], 'Additional content\n')

if __name__ == '__main__':
    unittest.main()
