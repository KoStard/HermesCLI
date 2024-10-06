import os
import importlib
import inspect
from typing import List, Type
from hermes.context_providers.base import ContextProvider
import logging

logger = logging.getLogger(__name__)

def load_extensions() -> List[Type[ContextProvider]]:
    providers = []
    extension_dir = os.path.expanduser("~/.config/hermes/extra_context_providers")
    
    if not os.path.exists(extension_dir):
        return providers

    for subfolder in os.listdir(extension_dir):
        subfolder_path = os.path.join(extension_dir, subfolder)
        if not os.path.isdir(subfolder_path):
            continue

        for filename in os.listdir(subfolder_path):
            try:
                if filename.endswith('.py'):
                    module_name = f"extra_context_providers.{subfolder}.{filename[:-3]}"
                    spec = importlib.util.spec_from_file_location(module_name, os.path.join(subfolder_path, filename))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, ContextProvider) and obj != ContextProvider:
                            providers.append(obj)
            except Exception as e:
                logger.warning(f"Error during loading of extension {subfolder}/{filename}: {str(e)}")

    return providers
