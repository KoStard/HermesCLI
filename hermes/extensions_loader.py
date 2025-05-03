# This file is used to load extensions, which will have user and LLM control panel extra commands
# The folder we are looking for is ~/.config/hermes/extensions/*/extension.py
# From there we should import (if present) get_user_extra_commands and get_llm_extra_commands functions
# They should return a list of ControlPanelCommand
# In case of failures, just print an error notification and continue
# Use module import logic to import the extension

import importlib.util
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional, Type
import logging

# Removed appdirs import
from hermes.config_utils import get_extensions_dir_path
from hermes.interface.commands.command import Command
from hermes.interface.control_panel.base_control_panel import ControlPanelCommand


def load_extension_module(extension_path: Path) -> Optional[object]:
    """Load a Python module from a file path"""
    try:
        spec = importlib.util.spec_from_file_location(
            f"hermes_extension_{extension_path.parent.name}", extension_path
        )
        if spec is None or spec.loader is None:
            logging.warning(f"Failed to load extension spec from {extension_path}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logging.warning(f"Failed to load extension from {extension_path}: {str(e)}")
        return None


def get_extension_commands(
    module: object, function_name: str
) -> List[ControlPanelCommand]:
    """Get commands from an extension module using the specified function"""
    try:
        if hasattr(module, function_name):
            func = getattr(module, function_name)
            commands = func()
            if isinstance(commands, list):
                return commands
        else:
            logging.warning(
                f"Function {function_name} not found in extension module", module
            )
    except Exception as e:
        logging.warning(f"Failed to get commands from {function_name}: {str(e)}")
    return []


def load_extensions() -> tuple[
    List[ControlPanelCommand],
    List[ControlPanelCommand],
    List[callable],
    List[Type[Command]],
]:
    """
    Load all extensions and return their commands and utils
    Returns: (user_commands, llm_commands, utils_builders, deep_research_commands)
    """
    user_commands = []
    llm_commands = []
    utils_builders = []
    deep_research_commands = []

    extensions_dir = get_extensions_dir_path()
    if not extensions_dir.exists():
        logging.info(
            f"Extensions directory not found at {extensions_dir}, skipping extension loading."
        )
        return [], [], [], []

    # Scan for extension.py files in subdirectories
    for extension_dir in extensions_dir.iterdir():
        if not extension_dir.is_dir():
            continue

        extension_file = extension_dir / "extension.py"
        if not extension_file.exists():
            continue

        # Load the extension module
        module = load_extension_module(extension_file)
        if module is None:
            continue

        # Get commands and utils from the extension
        user_commands.extend(get_extension_commands(module, "get_user_extra_commands"))
        llm_commands.extend(get_extension_commands(module, "get_llm_extra_commands"))

        # Get deep research commands if available
        if hasattr(module, "get_deep_research_commands"):
            try:
                commands = module.get_deep_research_commands()
                if isinstance(commands, list):
                    deep_research_commands.extend(commands)
            except Exception as e:
                logging.warning(f"Failed to get deep research commands: {str(e)}")

        # Get utils builders if available
        if hasattr(module, "get_utils_builders"):
            try:
                utils = module.get_utils_builders()
                if isinstance(utils, list):
                    utils_builders.extend(utils)
            except Exception as e:
                logging.warning(f"Failed to get utils builders: {str(e)}")

    return user_commands, llm_commands, utils_builders, deep_research_commands
