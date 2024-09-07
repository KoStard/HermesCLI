from typing import Dict, Any

class HermesConfig:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

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
        if key not in config or config[key] is None:
            config[key] = default_value
    
    return config
