import unittest
from unittest.mock import Mock
import argparse
from hermes.context_providers.image_context_provider import ImageContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestImageContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = ImageContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        ImageContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with("--image", action="append", help=ImageContextProvider.get_help())

    def test_get_help(self):
        self.assertEqual(ImageContextProvider.get_help(), "Path to image file to include in the context")

    def test_load_context_from_cli_single(self):
        args = Mock(spec=argparse.Namespace)
        args.image = "image1.jpg"
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.image_paths, ["image1.jpg"])

    def test_load_context_from_cli_multiple(self):
        args = Mock(spec=argparse.Namespace)
        args.image = ["image1.jpg", "image2.png"]
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.image_paths, ["image1.jpg", "image2.png"])

    def test_load_context_from_string(self):
        self.provider.load_context_from_string(["image1.jpg", "image2.png"])
        
        self.assertEqual(self.provider.image_paths, ["image1.jpg", "image2.png"])

    def test_add_to_prompt(self):
        self.provider.image_paths = ["image1.jpg", "image2.png"]
        
        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_image.assert_any_call("image1.jpg", name="Image: image1.jpg")
        self.mock_prompt_builder.add_image.assert_any_call("image2.png", name="Image: image2.png")

    def test_get_command_key(self):
        self.assertEqual(ImageContextProvider.get_command_key(), "image")

if __name__ == '__main__':
    unittest.main()