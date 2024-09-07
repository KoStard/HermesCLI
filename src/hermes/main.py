#!/usr/bin/env python

import os
import yaml
from datetime import datetime
import sys
import argparse
import configparser
from typing import Dict
import os

from hermes.prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder
from hermes.prompt_builders.markdown_prompt_builder import MarkdownPromptBuilder
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder

if os.name == 'posix':
    import readline
elif os.name == 'nt':
    try:
        import pyreadline3 as readline
    except ImportError:
        print("Warning: pyreadline3 is not installed. Autocomplete functionality may be limited on Windows.")
        readline = None

from .utils.file_utils import process_file_name
from .file_processors.default import DefaultFileProcessor
from .file_processors.bedrock import BedrockFileProcessor
from .chat_models.claude import ClaudeModel
from .chat_models.bedrock import BedrockModel
from .chat_models.gemini import GeminiModel
from .chat_models.openai import OpenAIModel
from .chat_models.ollama import OllamaModel
from .chat_models.deepseek import DeepSeekModel
from .chat_models.reflection import ReflectionModel
from .chat_models.groq import GroqModel
from .ui.chat_ui import ChatUI
from .chat_application import ChatApplication
from .workflows.executor import WorkflowExecutor
from .context_orchestrator import ContextOrchestrator
from .context_provider_loader import load_context_providers
from .config import create_config_from_args, HermesConfig

def get_default_model(config):
    if 'BASE' in config and 'model' in config['BASE']:
        return config['BASE']['model']
    return None

def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application with workflow support")
    parser.add_argument("--model", choices=["claude", "bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral", "gemini", "openai", "ollama", "deepseek", "reflection", "groq"], help="Choose the model to use")
    parser.add_argument("--prompt", help="Prompt text to send immediately")
    parser.add_argument("--prompt-file", help="File containing prompt to send immediately")
    parser.add_argument("--append", "-a", help="Append to the specified file")
    parser.add_argument("--update", "-u", help="Update the specified file")
    parser.add_argument("--pretty", help="Print the output by rendering markdown", action="store_true")
    parser.add_argument("--workflow", help="Specify a workflow YAML file to execute")

    # Load context providers dynamically (including extensions)
    context_providers = load_context_providers()
    context_orchestrator = ContextOrchestrator(context_providers)

    # Add arguments from context providers (including extensions)
    context_orchestrator.add_arguments(parser)

    args = parser.parse_args()
    hermes_config = create_config_from_args(args)

    config = configparser.ConfigParser()
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "multillmchat")
    config_path = os.path.join(config_dir, "config.ini")
    os.makedirs(config_dir, exist_ok=True)
    config.read(config_path)

    if hermes_config.get('model') is None:
        hermes_config.set('model', get_default_model(config))
        if hermes_config.get('model') is None:
            parser.error("No model specified and no default model found in config. Use --model to specify a model or set a default in the config file.")

    # Load special command prompts
    special_command_prompts_path = os.path.join(os.path.dirname(__file__), "config", "special_command_prompts.yaml")
    with open(special_command_prompts_path, 'r') as f:
        special_command_prompts = yaml.safe_load(f)

    if hermes_config.get('workflow'):
        run_workflow(hermes_config, config)
    else:
        run_chat_application(hermes_config, config, special_command_prompts, context_orchestrator)

def custom_print(text, *args, **kwargs):
    print(text, flush=True, *args, **kwargs)

def run_workflow(hermes_config: HermesConfig, config):
    model, file_processor, prompt_builder = create_model_and_processors(hermes_config.get('model'), config)

    input_files = hermes_config.get('files', [])
    initial_prompt = hermes_config.get('prompt') or (open(hermes_config.get('prompt_file'), 'r').read().strip() if hermes_config.get('prompt_file') else "")

    executor = WorkflowExecutor(hermes_config.get('workflow'), model, prompt_builder, input_files, initial_prompt, custom_print)
    result = executor.execute()

    # Create /tmp/hermes/ directory if it doesn't exist
    os.makedirs('/tmp/hermes/', exist_ok=True)

    # Generate filename with matching name and date-time suffix
    filename = f"/tmp/hermes/{os.path.basename(hermes_config.get('workflow'))}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"

    # Save the report as a YAML file
    with open(filename, 'w') as f:
        yaml.dump(result, f)

    print(f"Workflow execution completed. Detailed report saved to {filename}")

def run_chat_application(hermes_config: HermesConfig, config, special_command_prompts, context_orchestrator):
    if hermes_config.get('model') is None:
        hermes_config.set('model', get_default_model(config))
    special_command: Dict[str, str] = {}
    if hermes_config.get('append'):
        special_command['append'] = hermes_config.get('append')
    elif hermes_config.get('update'):
        special_command['update'] = hermes_config.get('update')

    initial_prompt = None
    if hermes_config.get('prompt'):
        initial_prompt = hermes_config.get('prompt')
    elif hermes_config.get('prompt_file'):
        with open(hermes_config.get('prompt_file'), 'r') as f:
            initial_prompt = f.read().strip()

    model, file_processor, prompt_builder = create_model_and_processors(hermes_config.get('model'), config)

    # Load contexts from hermes_config
    context_orchestrator.load_contexts(hermes_config)

    ui = ChatUI(prints_raw=not hermes_config.get('pretty'))
    app = ChatApplication(model, ui, file_processor, prompt_builder, special_command_prompts, context_orchestrator)

    app.run(initial_prompt, special_command)

def create_model_and_processors(model_name: str, config: configparser.ConfigParser):
    if model_name == "claude":
        model = ClaudeModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name.startswith("bedrock-"):
        model_tag = '-'.join(model_name.split("-")[1:])
        model = BedrockModel(config, model_tag)
        file_processor = BedrockFileProcessor()
        prompt_builder = BedrockPromptBuilder(file_processor)
    elif model_name == "gemini":
        model = GeminiModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "openai":
        model = OpenAIModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "ollama":
        model = OllamaModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "deepseek":
        model = DeepSeekModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "reflection":
        model = ReflectionModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = MarkdownPromptBuilder(file_processor)
    elif model_name == "groq":
        model = GroqModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = MarkdownPromptBuilder(file_processor)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    return model, file_processor, prompt_builder

if __name__ == "__main__":
    main()
