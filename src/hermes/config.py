from typing import Dict, Any, List

class HermesConfig:
    def __init__(self, config: Dict[str, List[str]]):
        self._config = config

    def get(self, key: str, default=None) -> List[str] | None:
        return self._config.get(key, default)

    def set(self, key: str, value: str | List[str]):
        if type(value) is str:
            value = [value]
        self._config[key] = value
    
    def __iter__(self):
        return iter(self._config.keys())

def create_config_from_args(args) -> HermesConfig:
    config = {}
    raw_values = vars(args)
    for key, value in raw_values.items():
        if value is not None:
            if type(value) is str:
                value = [value]
            config[key] = value
    
    config = HermesConfig(config)
    
    return config
