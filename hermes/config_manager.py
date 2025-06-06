import configparser
import sys

from hermes.chat.interface.assistant.chat_assistant.command_status_override import ChatAssistantCommandStatusOverride
from hermes.utils.config_utils import get_config_path


class ConfigManager:
    def __init__(self):
        self.config = self._load_config()

    def get_config(self) -> configparser.ConfigParser:
        return self.config

    def get_command_status_overrides(self) -> dict[str, ChatAssistantCommandStatusOverride]:
        command_status_overrides: dict[str, ChatAssistantCommandStatusOverride] = {}
        if "BASE" in self.config and "llm_command_status_overrides" in self.config["BASE"]:
            try:
                raw_overrides = self.config["BASE"]["llm_command_status_overrides"].strip()
                if raw_overrides:
                    for override in raw_overrides.split(","):
                        command_id, status = override.split(":")
                        command_status_overrides[command_id.strip()] = ChatAssistantCommandStatusOverride(status.strip().upper())
            except Exception as e:
                print(f"Warning: Failed to parse llm_command_status_overrides from config: {e}")
        return command_status_overrides

    def get_default_model_info_string(self) -> str | None:
        if "BASE" not in self.config:
            return None
        base_section = self.config["BASE"]
        return base_section.get("model")

    def get_mcp_chat_assistant_servers(self) -> dict[str, str]:
        return self._get_mcp_servers("MCP_CHAT_ASSISTANT")

    def get_mcp_deep_research_servers(self) -> dict[str, str]:
        return self._get_mcp_servers("MCP_DEEP_RESEARCH")

    def _get_mcp_servers(self, section_name: str) -> dict[str, str]:
        servers = {}
        if section_name in self.config:
            for name, command in self.config[section_name].items():
                servers[name] = command
        return servers

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
