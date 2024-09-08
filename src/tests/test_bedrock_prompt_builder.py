import pytest
from unittest.mock import Mock, patch
from hermes.prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder
from hermes.file_processors.base import FileProcessor

@pytest.fixture
def mock_file_processor():
    return Mock(spec=FileProcessor)

@pytest.fixture
def bedrock_prompt_builder(mock_file_processor):
    return BedrockPromptBuilder(mock_file_processor)

def test_add_text(bedrock_prompt_builder):
    bedrock_prompt_builder.add_text("Hello, world!")
    assert bedrock_prompt_builder.contents == [{'text': 'Hello, world!\n'}]

def test_add_text_with_name(bedrock_prompt_builder):
    bedrock_prompt_builder.add_text("Hello, world!", name="greeting")
    assert bedrock_prompt_builder.contents == [{'text': 'greeting:\nHello, world!\n'}]

def test_add_file_binary(bedrock_prompt_builder, mock_file_processor):
    mock_file_processor.read_file.return_value = 'binary_content'
    bedrock_prompt_builder.add_file('test.pdf', 'test_doc')
    assert bedrock_prompt_builder.contents == [{
        'text': '<document name="test_doc">binary_content</document>'
    }]

def test_add_file_text(bedrock_prompt_builder, mock_file_processor):
    mock_file_processor.read_file.return_value = 'text_content'
    bedrock_prompt_builder.add_file('test.txt', 'test_doc')
    assert bedrock_prompt_builder.contents == [{
        'text': '<document name="test_doc">text_content</document>'
    }]

def test_add_image(bedrock_prompt_builder, mock_file_processor):
    mock_file_processor.read_file.return_value = b'image_content'
    bedrock_prompt_builder.add_image('test.jpg', 'test_image')
    assert bedrock_prompt_builder.contents == [{
        'image': {
            'format': 'jpg',
            'source': {
                'bytes': b'image_content'
            }
        }
    }]

def test_build_prompt(bedrock_prompt_builder):
    bedrock_prompt_builder.add_text("Hello")
    bedrock_prompt_builder.add_text("World")
    assert bedrock_prompt_builder.build_prompt() == [
        {'text': 'Hello\n'},
        {'text': 'World\n'}
    ]
