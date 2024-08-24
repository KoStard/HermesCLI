#!/usr/bin/env python

import os
import sys
import argparse
import configparser
from typing import Dict
import readline

from .utils.file_utils import process_file_name
from .file_processors.default import DefaultFileProcessor
from .file_processors.bedrock import BedrockFileProcessor
from .prompt_formatters.xml import XMLPromptFormatter
from .prompt_formatters.bedrock import BedrockPromptFormatter
from .chat_models.claude import ClaudeModel
from .chat_models.bedrock import BedrockModel
from .chat_models.gemini import GeminiModel
from .chat_models.openai import OpenAIModel
from .chat_models.ollama import OllamaModel
from .ui.chat_ui import ChatUI
from .chat_application import ChatApplication
from .cli.workflow_commands import add_workflow_arguments, execute_workflow

def get_default_model(config):
    if 'DEFAULT' in config and 'model' in config['DEFAULT']:
        return config['DEFAULT']['model']
    return None

def main():
    parser = argparse.ArgumentParser(description="Multi-model chat application with workflow support")
    parser.add_argument("--model", choices=["claude", "bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral", "gemini", "openai", "ollama"], help="Choose the model to use")
    parser.add_argument("files", nargs='*', help="Input files")
    parser.add_argument("--prompt", help="Prompt text to send immediately")
    parser.add_argument("--prompt-file", help="File containing prompt to send immediately")
    parser.add_argument("--append", "-a", help="Append to the specified file")
    parser.add_argument("--update", "-u", help="Update the specified file")
    parser.add_argument("--raw", "-r", help="Print the output without rendering markdown", action="store_true")
    parser.add_argument("--confirm-before-starting", help="Will confirm before sending the LLM requests, in case you want to prevent unnecessary calls", action="store_true")
    parser.add_argument("--workflow", help="Specify a workflow YAML file to execute")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config_path = os.path.expanduser("~/.config/multillmchat/config.ini")
    config.read(config_path)

    if args.model is None:
        args.model = get_default_model(config)
        if args.model is None:
            parser.error("No model specified and no default model found in config. Use --model to specify a model or set a default in the config file.")

    if args.workflow:
        run_workflow(args, config)
    else:
        run_chat_application(args, config)

def run_workflow(args, config):
    model, file_processor, prompt_formatter = create_model_and_processors(args.model, config)

    input_files = args.files
    initial_prompt = args.prompt or (open(args.prompt_file, 'r').read().strip() if args.prompt_file else "")

    executor = WorkflowExecutor(args.workflow, model, file_processor, prompt_formatter, input_files, initial_prompt)
    result = executor.execute()

    print("Workflow execution completed.")
    print("Final context:")
    for key, value in result.items():
        print(f"{key}: {value}")

def run_chat_application(args, config):
    processed_files = {process_file_name(file): file for file in args.files}

    special_command: Dict[str, str] = {}
    if args.append:
        special_command['append'] = args.append
        processed_files[process_file_name(args.append)] = args.append
    elif args.update:
        special_command['update'] = args.update
        processed_files[process_file_name(args.update)] = args.update

    initial_prompt = None
    if args.prompt:
        initial_prompt = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            initial_prompt = f.read().strip()

    if args.confirm_before_starting:
        confirm = input("Are you sure you want to continue? (y/n) ").lower()
        if confirm != 'y' and confirm != '':
            return

    model, file_processor, prompt_formatter = create_model_and_processors(args.model, config)

    ui = ChatUI(prints_raw=args.raw)
    app = ChatApplication(model, ui, file_processor, prompt_formatter)
    app.set_files(processed_files)
    app.run(initial_prompt, special_command if special_command else None)

def create_model_and_processors(model_name: str, config: configparser.ConfigParser):
    if model_name == "claude":
        model = ClaudeModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    elif model_name.startswith("bedrock-"):
        model_tag = '-'.join(model_name.split("-")[1:])
        model = BedrockModel(config, model_tag)
        file_processor = BedrockFileProcessor()
        prompt_formatter = BedrockPromptFormatter(file_processor)
    elif model_name == "gemini":
        model = GeminiModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    elif model_name == "openai":
        model = OpenAIModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    elif model_name == "ollama":
        model = OllamaModel(config)
        file_processor = DefaultFileProcessor()
        prompt_formatter = XMLPromptFormatter(file_processor)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    return model, file_processor, prompt_formatter

if __name__ == "__main__":
    main()
