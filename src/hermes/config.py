from typing import Dict, Any

class HermesConfig:
    def __init__(self, config: Dict[str, Any]):
        self._config = config

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value

def create_config_from_args(args) -> HermesConfig:
    config = HermesConfig(vars(args))
    
    # Ensure these keys exist with default values if not present
    defaults = {
        'files': [],
        'text': [],
        'url': [],
        'image': []
    }
    
    for key, default_value in defaults.items():
        if config.get(key) is None:
            config.set(key, default_value)
    
    return config
