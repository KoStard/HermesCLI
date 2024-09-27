#!/usr/bin/env python

import os
import yaml
from datetime import datetime
import argparse
import logging
from logging.handlers import RotatingFileHandler

from hermes.model_factory import create_model_and_processors
from hermes.registry import ModelRegistry

if os.name == 'posix':
    import readline
elif os.name == 'nt':
    try:
        import pyreadline3 as readline
    except ImportError:
        print("Warning: pyreadline3 is not installed. Autocomplete functionality may be limited on Windows.")
        readline = None

from .chat_ui import ChatUI
from .chat_application import ChatApplication
from .context_provider_loader import load_context_providers
from .config import create_config_from_args, HermesConfig

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create /tmp/hermes_logs/ directory if it doesn't exist
    os.makedirs('/tmp/hermes_logs/', exist_ok=True)

    # Create handlers
    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler('/tmp/hermes_logs/hermes_debug.log', maxBytes=10*1024*1024, backupCount=5)

    # Set levels
    console_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)

    # Create formatters and set them to handlers
    console_format = logging.Formatter('%(message)s')
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def main():

    parser = argparse.ArgumentParser(description="Multi-model chat application")
    parser.add_argument("--model", choices=ModelRegistry.get_available_models(), help="Choose the model to use (optional if configured in config.ini)")
    parser.add_argument("--pretty", help="Print the output by rendering markdown", action="store_true")
    parser.add_argument("--once", help="Run Hermes only once without entering the loop", action="store_true")
    parser.add_argument("--no-highlighting", help="Disable syntax highlighting for markdown output", action="store_true")

    # Load context providers dynamically (including extensions)
    context_provider_classes = load_context_providers()

    # Add arguments from context providers (including extensions)
    for provider_class in context_provider_classes:
        provider_class.add_argument(parser)

    args = parser.parse_args()
    
    setup_logger()
    
    hermes_config = create_config_from_args(args)

    run_chat_application(hermes_config, context_provider_classes)

def run_chat_application(hermes_config: HermesConfig, context_provider_classes):
    model_name = hermes_config.get('model')[0] if hermes_config.get('model') else None
    model, model_id, file_processor, prompt_builder_class = create_model_and_processors(model_name)

    ui = ChatUI(print_pretty=hermes_config.get('pretty'), use_highlighting=not hermes_config.get('no_highlighting'))
    app = ChatApplication(model, ui, file_processor, prompt_builder_class, context_provider_classes, hermes_config)

    if hermes_config.get('once'):
        app.run_once()
    else:
        app.run()


if __name__ == "__main__":
    main()
