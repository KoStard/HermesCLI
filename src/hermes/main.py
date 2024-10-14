import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import List, Type
from dotenv import load_dotenv

from hermes.context_providers import ContextProvider, get_all_context_providers
from hermes.extension_loader import load_extensions
from hermes.history_builder import HistoryBuilder
from hermes.meta_context_providers import load_meta_context_providers
from hermes.model_factory import create_model_and_processors
from hermes.registry import ModelRegistry
from hermes.utils.markdown_highlighter import MarkdownHighlighter
from importlib.metadata import version

__version__ = version("hermes-cli")

if os.name == 'posix':
    import readline
elif os.name == 'nt':
    try:
        import pyreadline3 as readline
    except ImportError:
        print("Warning: pyreadline3 is not installed. Autocomplete functionality may be limited on Windows.")
        readline = None

from .chat_application import ChatApplication
from .chat_ui import ChatUI


def build_context_provider_map(context_provider_classes):
    command_keys_map = {}
    for provider_class in context_provider_classes:
        command_keys = provider_class.get_command_key()
        if isinstance(command_keys, str):
            command_keys = [command_keys]
        for key in command_keys:
            key = key.strip()
            command_keys_map[key] = provider_class
    return command_keys_map


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
    return logger

def load_debug_headers():
    load_dotenv()
    return {
        'DISABLE_EXTENSIONS': os.getenv('HERMES_DEBUG_DISABLE_EXTENSIONS', 'false').lower() == 'true'
    }

def load_context_providers(disable_extensions=False) -> List[Type[ContextProvider]]:
    providers = get_all_context_providers()
    
    # Load extension providers only if not disabled
    if not disable_extensions:
        providers.extend(load_extensions())
    
    return providers

def main():
    parser = argparse.ArgumentParser(description="Hermes CLI")
    parser.add_argument("--model", choices=ModelRegistry.get_available_models(), help="Choose the model to use (optional if configured in config.ini)")
    parser.add_argument("--pretty", help="Print the output by rendering markdown", action="store_true")
    parser.add_argument("--once", help="Run Hermes only once without entering the loop", action="store_true")
    parser.add_argument("--no-highlighting", help="Disable syntax highlighting for markdown output", action="store_true")
    parser.add_argument("--load-history", help="Load chat history from a file", type=str, metavar="FILEPATH")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    # Load debug headers
    debug_headers = load_debug_headers()

    # Load context providers dynamically (including extensions if not disabled)
    context_provider_classes = load_context_providers(disable_extensions=debug_headers['DISABLE_EXTENSIONS'])

    # Add arguments from context providers (including extensions)
    for provider_class in context_provider_classes:
        provider_class.add_argument(parser)
        
    meta_context_providers = load_meta_context_providers()
    context_provider_classes.extend(meta_context_providers)

    args = parser.parse_args()
    
    logger = setup_logger()

    model_name = args.model
    try:    
        model, file_processor, prompt_builder_class = create_model_and_processors(model_name)
    except Exception as e:
        logger.error(f"Error creating model and processors: {str(e)}")
        sys.exit(1)

    command_keys_map = build_context_provider_map(context_provider_classes)
    history_builder = HistoryBuilder(prompt_builder_class, file_processor, command_keys_map)

    logger.info(f"Using model {model.model_tag} with class {model.__class__.__name__}")
    logger.info(f"Using file processor: {type(file_processor).__name__}")
    logger.info(f"Using prompt builder: {prompt_builder_class.__name__}")
    
    ui = ChatUI(print_pretty=args.pretty, use_highlighting=not args.no_highlighting, markdown_highlighter=MarkdownHighlighter())
    app = ChatApplication(model, ui, history_builder, command_keys_map, args)
    app.run_chat(args.once)

if __name__ == "__main__":
    main()
