import os
import importlib
import inspect
from typing import List
from hermes.context_providers.base import ContextProvider
from hermes.extension_loader import load_extensions

def load_context_providers() -> List[Type[ContextProvider]]:
    providers = []
    provider_dir = os.path.join(os.path.dirname(__file__), 'context_providers')
    
    # Load built-in providers
    for filename in os.listdir(provider_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = f'hermes.context_providers.{filename[:-3]}'
            module = importlib.import_module(module_name)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, ContextProvider) and obj != ContextProvider:
                    providers.append(obj)
    
    # Load extension providers
    providers.extend(load_extensions())
    
    return providers
