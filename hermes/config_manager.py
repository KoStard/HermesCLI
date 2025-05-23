import configparser
import sys

from hermes.utils.config_utils import get_config_path


class ConfigManager:
    def __init__(self):
        self.config = self._load_config()

    def get_config(self) -> configparser.ConfigParser:
        return self.config

    def get_command_status_overrides(self) -> dict[str, str]:
        command_status_overrides = {}
        if "BASE" in self.config and "llm_command_status_overrides" in self.config["BASE"]:
            try:
                raw_overrides = self.config["BASE"]["llm_command_status_overrides"].strip()
                if raw_overrides:
                    for override in raw_overrides.split(","):
                        command_id, status = override.split(":")
                        command_status_overrides[command_id.strip()] = status.strip().upper()
            except Exception as e:
                print(f"Warning: Failed to parse llm_command_status_overrides from config: {e}")
        return command_status_overrides

    def get_default_model_info_string(self) -> str | None:
        if "BASE" not in self.config:
            return None
        base_section = self.config["BASE"]
        return base_section.get("model")

    def _load_config(self) -> configparser.ConfigParser:
        config_path = get_config_path()

        if not config_path.exists():
            expected_path_str = str(config_path)
            error_message = (
                f"Configuration file not found.\n"
                f"Hermes expects it at the following location for your OS ({sys.platform}):\n"
                f"  -> {expected_path_str}\n\n"
                f"Please create the directory and the 'config.ini' file.\n"
                "Refer to the documentation for setup instructions: https://github.com/KoStard/HermesCLI/"
            )
            raise ValueError(error_message)

        config = configparser.ConfigParser()
        config.read(config_path)
        return config