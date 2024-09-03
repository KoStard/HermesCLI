import unittest
from unittest.mock import MagicMock, patch
from hermes.prompt_formatters.xml import XMLPromptFormatter
from hermes.prompt_formatters.bedrock import BedrockPromptFormatter
from hermes.file_processors.default import DefaultFileProcessor
from hermes.file_processors.bedrock import BedrockFileProcessor
import xml.etree.ElementTree as ET

class TestXMLPromptFormatter(unittest.TestCase):
    def setUp(self):
        self.file_processor = MagicMock(spec=DefaultFileProcessor)
        self.formatter = XMLPromptFormatter(self.file_processor)

    @patch('hermes.prompt_formatters.bedrock.is_binary', return_value=False)
    def test_format_prompt_text(self, mock_is_binary):
        files = {'test_file': 'path/to/test_file.txt'}
        prompt = 'Test prompt'
        self.file_processor.read_file.return_value = b"File content"

        self.file_processor.read_file.return_value = "File content"

        result = self.formatter.format_prompt(files, prompt)

        root = ET.fromstring(result)
        self.assertEqual(root.tag, 'input')
        self.assertEqual(root.find('systemMessage').text, "You are a helpful assistant, helping with the requests your manager will assign to you. You gain bonus at the end of each week if you meaningfully help your manager with his goals.")
        self.assertEqual(root.find('document').attrib['name'], 'test_file')
        self.assertEqual(root.find('document').text, 'File content')
        self.assertEqual(root.find('prompt').text, 'Test prompt')

    def test_format_prompt_with_special_command(self):
        files = {'output.txt': 'path/to/output.txt'}
        prompt = 'Test prompt'
        special_command = {'append': 'output.txt'}
        self.file_processor.read_file.return_value = "File content"

        result = self.formatter.format_prompt(files, prompt, special_command)

        root = ET.fromstring(result)
        self.assertEqual(root.find('specialCommand/append').text, 'output.txt')
        self.assertEqual(root.findall('prompt')[-1].text, "Please provide only the text that should be appended to the file 'output.txt'. Do not include any explanations or additional comments.")

    def test_format_prompt_with_text_inputs(self):
        files = {}
        prompt = 'Test prompt'
        text_inputs = ['Input 1', 'Input 2']

        result = self.formatter.format_prompt(files, prompt, text_inputs=text_inputs)

        root = ET.fromstring(result)
        text_inputs_elem = root.find('text_inputs')
        self.assertIsNotNone(text_inputs_elem)
        self.assertEqual([elem.text for elem in text_inputs_elem.findall('text')], text_inputs)

    def test_add_content(self):
        current = '<input><prompt>Initial prompt</prompt></input>'
        content_to_add = 'Additional content'
        result = self.formatter.add_content(current, content_to_add)

        root = ET.fromstring(result)
        prompts = root.findall('prompt')
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0].text, 'Initial prompt')
        self.assertEqual(prompts[1].text, 'Additional content')

class TestBedrockPromptFormatter(unittest.TestCase):
    def setUp(self):
        self.file_processor = MagicMock(spec=BedrockFileProcessor)
        self.formatter = BedrockPromptFormatter(self.file_processor)

    @patch('hermes.prompt_formatters.bedrock.is_binary', return_value=False)
    def test_format_prompt_text(self, mock_is_binary):
        files = {'test_file': 'path/to/test_file.txt'}
        prompt = 'Test prompt'
        self.file_processor.read_file.return_value = b"File content"

        self.file_processor.read_file.return_value = "File content"

        result = self.formatter.format_prompt(files, prompt)

        self.assertEqual(len(result), 2)
        self.assertIn('text', result[0])
        self.assertIn('<document name="test_file">', result[0]['text'])
        self.assertIn('File content', result[0]['text'])
        self.assertEqual(result[1], {'text': 'Test prompt\n'})

    @patch('hermes.prompt_formatters.bedrock.is_binary', return_value=True)
    def test_format_prompt_image(self, mock_is_binary):
        files = {'test_image': 'path/to/test_image.png'}
        prompt = 'Describe the image'
        self.file_processor.read_file.return_value = b"image_bytes"

        result = self.formatter.format_prompt(files, prompt)

        self.assertEqual(len(result), 2)
        self.assertIn('image', result[0])
        self.assertEqual(result[0]['image']['format'], 'png')
        self.assertEqual(result[0]['image']['source']['bytes'], b"image_bytes")
        self.assertEqual(result[1], {'text': 'Describe the image\n'})

    def test_format_prompt_with_special_command(self):
        files = {'output.txt': 'path/to/output.txt'}
        prompt = 'Test prompt'
        special_command = {'append': 'output.txt'}
        self.file_processor.read_file.return_value = b"File content"

        result = self.formatter.format_prompt(files, prompt, special_command)

        self.assertEqual(len(result), 3)
        self.assertIn('Please provide only the text that should be appended to the file', result[2]['text'])

    def test_format_prompt_with_text_inputs(self):
        files = {}
        prompt = 'Test prompt'
        text_inputs = ['Input 1', 'Input 2']

        result = self.formatter.format_prompt(files, prompt, text_inputs=text_inputs)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {'text': 'Test prompt\n'})
        self.assertIn('Additional text inputs:', result[1]['text'])
        self.assertIn('Input 1', result[1]['text'])
        self.assertIn('Input 2', result[1]['text'])

    def test_add_content(self):
        content_to_add = 'Additional content'
        current = [{'text': 'Initial prompt'}]
        result = self.formatter.add_content(current, content_to_add)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {'text': 'Initial prompt'})
        self.assertEqual(result[1], {'text': 'Additional content\n'})

if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()
