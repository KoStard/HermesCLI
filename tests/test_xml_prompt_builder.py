import unittest
from unittest.mock import Mock
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder
from hermes.file_processors.base import FileProcessor

class TestXMLPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.file_processor = Mock(spec=FileProcessor)
        self.prompt_builder = XMLPromptBuilder(self.file_processor)

    def test_add_text(self):
        self.prompt_builder.add_text("Hello, world!")
        prompt = self.prompt_builder.build_prompt()
        self.assertIn("<text>Hello, world!</text>", prompt)

    def test_add_text_with_name(self):
        self.prompt_builder.add_text("Hello, world!", name="greeting")
        prompt = self.prompt_builder.build_prompt()
        self.assertIn('<text name="greeting">Hello, world!</text>', prompt)

    def test_add_file(self):
        self.file_processor.read_file.return_value = "File content"
        self.prompt_builder.add_file("test.txt", "test_file")
        prompt = self.prompt_builder.build_prompt()
        self.assertIn('<document name="test_file">File content</document>', prompt)

    def test_build_prompt(self):
        self.prompt_builder.add_text("Hello")
        self.prompt_builder.add_text("World", name="greeting")
        prompt = self.prompt_builder.build_prompt()
        self.assertIn("<root>", prompt)
        self.assertIn("<input>", prompt)
        self.assertIn("<text>Hello</text>", prompt)
        self.assertIn('<text name="greeting">World</text>', prompt)

    def test_erase(self):
        self.prompt_builder.add_text("Hello")
        self.prompt_builder.erase()
        prompt = self.prompt_builder.build_prompt()
        self.assertNotIn("<text>Hello</text>", prompt)

if __name__ == '__main__':
    unittest.main()
