import json
import sys
from typing import Any

from hermes.chat.interface.assistant.chat.command_status_override import ChatAssistantCommandStatusOverride
from hermes.utils.config_utils import get_json_config_path


class JsonConfigManager:
    def __init__(self):
        self.config = self._load_config()

    def get_config(self) -> dict[str, Any]:
        return self.config

    def get_command_status_overrides(self) -> dict[str, ChatAssistantCommandStatusOverride]:
        command_status_overrides: dict[str, ChatAssistantCommandStatusOverride] = {}

        # Check for overrides in top level
        if "llm_command_status_overrides" in self.config:
            try:
                overrides_config = self.config["llm_command_status_overrides"]
                command_status_overrides.update(self._parse_overrides(overrides_config))
            except Exception as e:
                print(f"Warning: Failed to parse top-level llm_command_status_overrides from config: {e}")

        # Check for overrides in base section
        base_config = self.config.get("base", {})
        if "llm_command_status_overrides" in base_config:
            try:
                overrides_config = base_config["llm_command_status_overrides"]
                command_status_overrides.update(self._parse_overrides(overrides_config))
            except Exception as e:
                print(f"Warning: Failed to parse base section llm_command_status_overrides from config: {e}")

        return command_status_overrides

    def _parse_overrides(self, overrides_config) -> dict[str, ChatAssistantCommandStatusOverride]:
        result = {}
        if isinstance(overrides_config, dict):
            for command_id, status in overrides_config.items():
                result[command_id] = ChatAssistantCommandStatusOverride(status.upper())
        elif isinstance(overrides_config, str) and overrides_config.strip():
            # Support legacy string format
            for override in overrides_config.split(","):
                if ":" in override:
                    command_id, status = override.split(":")
                    result[command_id.strip()] = ChatAssistantCommandStatusOverride(status.strip().upper())
        return result

    def get_default_model_info_string(self) -> str | None:
        # Check for model in the top level and in the base section
        model = self.config.get("model")
        if model:
            return model

        # Check in base section
        base_config = self.config.get("base", {})
        return base_config.get("model")

    def get_mcp_chat_assistant_servers(self) -> dict[str, dict[str, Any] | str]:
        return self.config.get("mcp_chat_assistant", {})

    def get_mcp_deep_research_servers(self) -> dict[str, dict[str, Any] | str]:
        return self.config.get("mcp_deep_research", {})

    def get_mcp_server_tool_config(self, server_name: str, server_config: dict[str, Any] | str) -> dict[str, bool]:
        """
        Extract tool configuration from MCP server configuration.
        Returns a dictionary mapping tool names to boolean values (True for enabled, False for disabled).
        An empty dict means no filtering (all tools enabled).
        """
        if isinstance(server_config, str):
            return {}  # No tool configuration for simple string configs

        # Check for tools configuration section
        tools_config = server_config.get("tools", {})
        if not tools_config:
            return {}

        # Handle different configuration formats
        if isinstance(tools_config, list):
            # List of tool names to enable
            return {tool_name: True for tool_name in tools_config}
        if isinstance(tools_config, dict):
            # Dictionary mapping tool names to enable/disable status
            return tools_config

        return {}

    def get_exa_api_key(self) -> str | None:
        exa_config = self.config.get("exa", {})
        return exa_config.get("api_key")

    def get_groq_api_key(self) -> str | None:
        groq_config = self.config.get("groq", {})
        return groq_config.get("api_key")

    def _load_config(self) -> dict[str, Any]:
        config_path = get_json_config_path()

        if not config_path.exists():
            expected_path_str = str(config_path)
            error_message = (
                f"Configuration file not found.\n"
                f"Hermes expects it at the following location for your OS ({sys.platform}):\n"
                f"  -> {expected_path_str}\n\n"
                f"Please create the directory and the 'config.json' file.\n"
                "Refer to the documentation for setup instructions: https://github.com/KoStard/HermesCLI/"
            )
            raise ValueError(error_message)

        with open(config_path) as f:
            return json.load(f)
