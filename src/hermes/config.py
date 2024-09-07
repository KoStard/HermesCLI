from typing import Dict, Any

class HermesConfig(dict):
    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, value):
        self[name] = value

def create_config_from_args(args):
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
