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
from .ui.chat_ui import ChatUI
from .chat_application import ChatApplication
from .workflows.executor import WorkflowExecutor
from .context_orchestrator import ContextOrchestrator
from .context_providers.file_context_provider import FileContextProvider
from .context_providers.text_context_provider import TextContextProvider

def get_default_model(config):
    if 'BASE' in config and 'model' in config['BASE']:
        return config['BASE']['model']
    return None

def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application with workflow support")
    parser.add_argument("--model", choices=["claude", "bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral", "gemini", "openai", "ollama", "deepseek"], help="Choose the model to use")
    parser.add_argument("--prompt", help="Prompt text to send immediately")
    parser.add_argument("--prompt-file", help="File containing prompt to send immediately")
    parser.add_argument("--append", "-a", help="Append to the specified file")
    parser.add_argument("--update", "-u", help="Update the specified file")
    parser.add_argument("--pretty", help="Print the output by rendering markdown", action="store_true")
    parser.add_argument("--workflow", help="Specify a workflow YAML file to execute")

    # Create context providers
    file_provider = FileContextProvider()
    text_provider = TextContextProvider()
    context_orchestrator = ContextOrchestrator([file_provider, text_provider])

    # Add arguments from context providers
    context_orchestrator.add_arguments(parser)

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "multillmchat")
    config_path = os.path.join(config_dir, "config.ini")
    os.makedirs(config_dir, exist_ok=True)
    config.read(config_path)

    if args.model is None:
        args.model = get_default_model(config)
        if args.model is None:
            parser.error("No model specified and no default model found in config. Use --model to specify a model or set a default in the config file.")

    # Load special command prompts
    special_command_prompts_path = os.path.join(os.path.dirname(__file__), "config", "special_command_prompts.yaml")
    with open(special_command_prompts_path, 'r') as f:
        special_command_prompts = yaml.safe_load(f)

    if args.workflow:
        run_workflow(args, config)
    else:
        run_chat_application(args, config, special_command_prompts, context_orchestrator)

def custom_print(text, *args, **kwargs):
    print(text, flush=True, *args, **kwargs)

def run_workflow(args, config):
    model, file_processor, prompt_builder = create_model_and_processors(args.model, config)

    input_files = args.files
    initial_prompt = args.prompt or (open(args.prompt_file, 'r').read().strip() if args.prompt_file else "")

    executor = WorkflowExecutor(args.workflow, model, prompt_builder, input_files, initial_prompt, custom_print)
    result = executor.execute()

    # Create /tmp/hermes/ directory if it doesn't exist
    os.makedirs('/tmp/hermes/', exist_ok=True)

    # Generate filename with matching name and date-time suffix
    filename = f"/tmp/hermes/{os.path.basename(args.workflow)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"

    # Save the report as a YAML file
    with open(filename, 'w') as f:
        yaml.dump(result, f)

    print(f"Workflow execution completed. Detailed report saved to {filename}")

def run_chat_application(args, config, special_command_prompts, context_orchestrator):
    if args.model is None:
        args.model = get_default_model(config)
    special_command: Dict[str, str] = {}
    if args.append:
        special_command['append'] = process_file_name(args.append)
    elif args.update:
        special_command['update'] = process_file_name(args.update)

    initial_prompt = None
    if args.prompt:
        initial_prompt = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            initial_prompt = f.read().strip()

    model, file_processor, prompt_builder = create_model_and_processors(args.model, config)

    # Load contexts from arguments
    context_orchestrator.load_contexts(args)

    ui = ChatUI(prints_raw=not args.pretty)
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
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    return model, file_processor, prompt_builder

if __name__ == "__main__":
    main()
