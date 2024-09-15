import pytest
from argparse import ArgumentParser
from unittest.mock import Mock

from hermes.context_providers.image_context_provider import ImageContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestImageContextProvider:
    @pytest.fixture
    def image_provider(self):
        return ImageContextProvider()

    def test_add_argument(self, image_provider):
        parser = ArgumentParser()
        image_provider.add_argument(parser)
        args = parser.parse_args(['--image', 'image1.jpg', '--image', 'image2.png'])
        assert args.image == ['image1.jpg', 'image2.png']

    def test_load_context(self, image_provider):
        args = Mock()
        args.get.return_value = ['image1.jpg', 'image2.png']
        image_provider.load_context(args)
        assert image_provider.image_paths == ['image1.jpg', 'image2.png']

    def test_load_context_no_images(self, image_provider):
        args = Mock()
        args.get.return_value = []
        image_provider.load_context(args)
        assert image_provider.image_paths == []

    def test_add_to_prompt(self, image_provider):
        image_provider.image_paths = ['image1.jpg', 'image2.png']
        mock_prompt_builder = Mock(spec=PromptBuilder)
        image_provider.add_to_prompt(mock_prompt_builder)
        mock_prompt_builder.add_image.assert_any_call('image1.jpg', name='Image: image1.jpg')
        mock_prompt_builder.add_image.assert_any_call('image2.png', name='Image: image2.png')
        assert mock_prompt_builder.add_image.call_count == 2

    def test_is_used(self, image_provider):
        image_provider.image_paths = []
        assert not image_provider.is_used()
        
        image_provider.image_paths = ['image1.jpg']
        assert image_provider.is_used()
