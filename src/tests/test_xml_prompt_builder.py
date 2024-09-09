import unittest
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder
from hermes.file_processors.base import FileProcessor

class TestXMLPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.mock_file_processor = MagicMock(spec=FileProcessor)
        self.xml_prompt_builder = XMLPromptBuilder(self.mock_file_processor)

    def test_add_text(self):
        self.xml_prompt_builder.add_text("Hello, world!")
        prompt = self.xml_prompt_builder.build_prompt()
        root = ET.fromstring(prompt)
        self.assertIn('Hello, world!', [text.text for text in root.findall('input/text')])

    def test_add_text_with_name(self):
        self.xml_prompt_builder.add_text("Hello, world!", name="greeting")
        prompt = self.xml_prompt_builder.build_prompt()
        root = ET.fromstring(prompt)
        self.assertEqual(root.find('input/text[@name="greeting"]').text, "Hello, world!")

    def test_add_file(self):
        self.mock_file_processor.read_file.return_value = "File content"
        self.xml_prompt_builder.add_file("/path/to/file.txt", "test_file")
        prompt = self.xml_prompt_builder.build_prompt()
        root = ET.fromstring(prompt)
        self.assertEqual(root.find('input/document[@name="test_file"]').text, "File content")
        self.mock_file_processor.read_file.assert_called_once_with("/path/to/file.txt")

    def test_add_image(self):
        with self.assertRaises(NotImplementedError):
            self.xml_prompt_builder.add_image("/path/to/image.jpg", "test_image")

    def test_build_prompt(self):
        self.xml_prompt_builder.add_text("Hello")
        self.mock_file_processor.read_file.return_value = "File content"
        self.xml_prompt_builder.add_file("/path/to/file.txt", "test_file")
        prompt = self.xml_prompt_builder.build_prompt()
        root = ET.fromstring(prompt)
        self.assertEqual(root.tag, "root")
        self.assertEqual(len(root.findall('input/*')), 2)  # text, document
        self.assertIn('Hello', [text.text for text in root.findall('input/text')])
        self.assertEqual(root.find('input/document[@name="test_file"]').text, "File content")

if __name__ == '__main__':
    unittest.main()
