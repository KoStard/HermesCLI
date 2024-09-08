#!/usr/bin/env python

import os
import yaml
from datetime import datetime
import sys
import argparse
import configparser
from typing import Dict
import os

from hermes.model_factory import create_model_and_processors

if os.name == 'posix':
    import readline
elif os.name == 'nt':
    try:
        import pyreadline3 as readline
    except ImportError:
        print("Warning: pyreadline3 is not installed. Autocomplete functionality may be limited on Windows.")
        readline = None

from .utils.file_utils import process_file_name
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

    # Load special command prompts
    special_command_prompts_path = os.path.join(os.path.dirname(__file__), "config", "special_command_prompts.yaml")
    with open(special_command_prompts_path, 'r') as f:
        special_command_prompts = yaml.safe_load(f)

    if hermes_config.get('workflow'):
        run_workflow(hermes_config)
    else:
        run_chat_application(hermes_config, special_command_prompts, context_orchestrator)

def custom_print(text, *args, **kwargs):
    print(text, flush=True, *args, **kwargs)

def run_workflow(hermes_config: HermesConfig):
    model, model_id, prompt_builder = create_model_and_processors(hermes_config.get('model'))

    input_files = hermes_config.get('files', [])
    initial_prompt = hermes_config.get('prompt')
    if not initial_prompt and hermes_config.get('prompt_file'):
        with open(hermes_config.get('prompt_file')) as f:
            initial_prompt = f.read().strip()

    executor = WorkflowExecutor(hermes_config.get('workflow'), model, model_id, prompt_builder, input_files, initial_prompt, custom_print)
    result = executor.execute()

    # Create /tmp/hermes/ directory if it doesn't exist
    os.makedirs('/tmp/hermes/', exist_ok=True)

    # Generate filename with matching name and date-time suffix
    filename = f"/tmp/hermes/{os.path.basename(hermes_config.get('workflow'))}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"

    # Save the report as a YAML file
    with open(filename, 'w') as f:
        yaml.dump(result, f)

    print(f"Workflow execution completed. Detailed report saved to {filename}")

def run_chat_application(hermes_config: HermesConfig, special_command_prompts, context_orchestrator):
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

    model, model_id, prompt_builder = create_model_and_processors(hermes_config.get('model'))

    # Load contexts from hermes_config
    context_orchestrator.load_contexts(hermes_config)

    ui = ChatUI(prints_raw=not hermes_config.get('pretty'))
    app = ChatApplication(model, ui, prompt_builder, special_command_prompts, context_orchestrator)

    app.run(initial_prompt, special_command)


if __name__ == "__main__":
    main()
