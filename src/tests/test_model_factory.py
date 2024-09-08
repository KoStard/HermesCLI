import pytest
from unittest.mock import patch, MagicMock
from hermes.model_factory import create_model_and_processors
from hermes.chat_models.claude import ClaudeModel
from hermes.chat_models.bedrock import BedrockModel
from hermes.chat_models.gemini import GeminiModel
from hermes.chat_models.openai import OpenAIModel
from hermes.chat_models.ollama import OllamaModel
from hermes.prompt_builders.claude_prompt_builder import ClaudePromptBuilder
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder
from hermes.prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder

@pytest.fixture
def mock_config():
    return MagicMock()

@patch('hermes.model_factory.configparser.ConfigParser')
def test_claude_model(mock_config_parser, mock_config):
    mock_config_parser.return_value = mock_config
    model, model_name, prompt_builder = create_model_and_processors("claude")
    assert isinstance(model, ClaudeModel)
    assert isinstance(prompt_builder, ClaudePromptBuilder)

@patch('hermes.model_factory.configparser.ConfigParser')
def test_bedrock_models(mock_config_parser, mock_config):
    mock_config_parser.return_value = mock_config
    bedrock_models = ["bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral"]
    for model_name in bedrock_models:
        model, model_name, prompt_builder = create_model_and_processors(model_name)
        assert isinstance(model, BedrockModel)
        assert model.model_tag == model_name.split("-", 1)[1]
        assert isinstance(prompt_builder, BedrockPromptBuilder)

@patch('hermes.model_factory.configparser.ConfigParser')
def test_other_models(mock_config_parser, mock_config):
    mock_config_parser.return_value = mock_config
    model_classes = {
        "gemini": GeminiModel,
        "ollama": OllamaModel,
        "openai": OpenAIModel
    }
    for model_name, model_class in model_classes.items():
        model, model_name, prompt_builder = create_model_and_processors(model_name)
        assert isinstance(model, model_class)
        assert isinstance(prompt_builder, XMLPromptBuilder)

@patch('hermes.model_factory.configparser.ConfigParser')
def test_unsupported_model(mock_config_parser, mock_config):
    mock_config_parser.return_value = mock_config
    with pytest.raises(ValueError):
        create_model_and_processors("unsupported-model")
