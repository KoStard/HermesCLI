# This file is used to load extensions, which will have user and LLM control panel extra commands
# The folder we are looking for is ~/.config/hermes/extensions/*/extension.py
# From there we should import (if present) get_user_extra_commands and get_llm_extra_commands functions
# They should return a list of ControlPanelCommand
# In case of failures, just print an error notification and continue
# Use module import logic to import the extension

import importlib.util
import logging
import sys
from collections import namedtuple
from pathlib import Path
from types import ModuleType

from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.utils.config_utils import get_extensions_dir_path

Extensions = namedtuple("Extensions", ["user_commands", "llm_commands", "utils_builders", "deep_research_commands"])


class ExtensionsLoader:
    def __init__(self) -> None:
        self.user_commands = []
        self.llm_commands = []
        self.utils_builders = []
        self.deep_research_commands = []

    def load_extensions(self) -> Extensions:
        """Load all extensions and return their commands and utils
        Returns: (user_commands, llm_commands, utils_builders, deep_research_commands)
        """
        root_directory = get_extensions_dir_path()
        if not root_directory.exists():
            logging.info(f"Extensions directory not found at {root_directory}, skipping extension loading.")
            return self._assemble_extensions_object()

        extension_directories = self._list_extension_directories(root_directory)
        self._load_extensions_from_directories(extension_directories)
        return self._assemble_extensions_object()

    def _assemble_extensions_object(self) -> Extensions:
        return Extensions(self.user_commands, self.llm_commands, self.utils_builders, self.deep_research_commands)

    def _list_extension_directories(self, root_dir: Path) -> list[Path]:
        directories = []
        for path in root_dir.iterdir():
            if path.is_dir():
                directories.append(path)
        return directories

    def _load_extensions_from_directories(self, extension_directories: list[Path]):
        # Scan for extension.py files in subdirectories
        for extension_dir in extension_directories:
            extension_file = extension_dir / "extension.py"
            if not extension_file.exists():
                continue

            # Load the extension module
            module = self._load_extension_module(extension_file)
            if module is None:
                continue

            # Get commands and utils from the extension
            self.user_commands.extend(self._get_extension_commands(module, "get_user_extra_commands"))
            self.llm_commands.extend(self._get_extension_commands(module, "get_llm_extra_commands"))
            self.deep_research_commands.extend(self._get_extension_commands(module, "get_deep_research_commands"))
            self.utils_builders.extend(self._get_extension_commands(module, "get_utils_builders"))

    def _load_extension_module(self, extension_path: Path) -> ModuleType | None:
        """Load a Python module from a file path"""
        try:
            spec = importlib.util.spec_from_file_location(f"hermes_extension_{extension_path.parent.name}", extension_path)
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

    def _get_extension_commands(self, module: ModuleType, function_name: str) -> list[ControlPanelCommand]:
        """Get commands from an extension module using the specified function"""
        try:
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                commands = func()
                if isinstance(commands, list):
                    return commands
            else:
                logging.warning(f"Function {function_name} not found in extension module", module)
        except Exception as e:
            logging.warning(f"Failed to get commands from {function_name}: {str(e)}")
        return []
