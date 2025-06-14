import configparser
import sys
from typing import Any

from hermes.chat.interface.assistant.chat.command_status_override import ChatAssistantCommandStatusOverride
from hermes.json_config_manager import JsonConfigManager
from hermes.utils.config_utils import get_json_config_path, get_legacy_config_path


class ConfigManager:
    def __init__(self):
        self._json_config_manager = None
        self._ini_config_manager = None
        self._determine_config_source()

    def _determine_config_source(self):
        json_config_path = get_json_config_path()
        ini_config_path = get_legacy_config_path()

        if json_config_path.exists():
            self._json_config_manager = JsonConfigManager()
        elif ini_config_path.exists():
            self._ini_config_manager = self._load_ini_config()
        else:
            # Neither exists - raise error for JSON (preferred format)
            expected_json_path_str = str(json_config_path)
            expected_ini_path_str = str(ini_config_path)
            error_message = (
                f"Configuration file not found.\n"
                f"Hermes expects it at one of the following locations for your OS ({sys.platform}):\n"
                f"  -> {expected_json_path_str} (preferred)\n"
                f"  -> {expected_ini_path_str} (legacy)\n\n"
                f"Please create the directory and either 'config.json' or 'config.ini' file.\n"
                "Refer to the documentation for setup instructions: https://github.com/KoStard/HermesCLI/"
            )
            raise ValueError(error_message)

    def get_config(self) -> configparser.ConfigParser | dict[str, Any]:
        if self._json_config_manager:
            return self._json_config_manager.get_config()
        return self._ini_config_manager

    def get_command_status_overrides(self) -> dict[str, ChatAssistantCommandStatusOverride]:
        if self._json_config_manager:
            return self._json_config_manager.get_command_status_overrides()
        return self._extract_ini_command_overrides()

    def _extract_ini_command_overrides(self) -> dict[str, ChatAssistantCommandStatusOverride]:
        command_status_overrides: dict[str, ChatAssistantCommandStatusOverride] = {}
        if (
            self._ini_config_manager
            and "BASE" in self._ini_config_manager
            and "llm_command_status_overrides" in self._ini_config_manager["BASE"]
        ):
            try:
                raw_overrides = self._ini_config_manager["BASE"]["llm_command_status_overrides"].strip()
                self._add_command_overrides_string(raw_overrides, command_status_overrides)
            except Exception as e:
                print(f"Warning: Failed to parse llm_command_status_overrides from config: {e}")
        return command_status_overrides

    def _add_command_overrides_string(self, raw_overrides: str, command_status_overrides: dict[str, ChatAssistantCommandStatusOverride]):
        if not raw_overrides:
            return
        for override in raw_overrides.split(","):
            command_id, status = override.split(":")
            command_status_overrides[command_id.strip()] = ChatAssistantCommandStatusOverride(status.strip().upper())

    def get_default_model_info_string(self) -> str | None:
        if self._json_config_manager:
            return self._json_config_manager.get_default_model_info_string()

        if not self._ini_config_manager or "BASE" not in self._ini_config_manager:
            return None
        base_section = self._ini_config_manager["BASE"]
        return base_section.get("model")

    def get_mcp_chat_assistant_servers(self) -> dict[str, dict[str, Any] | str]:
        if self._json_config_manager:
            return self._json_config_manager.get_mcp_chat_assistant_servers()
        # MCP not supported in INI config
        return {}

    def get_mcp_deep_research_servers(self) -> dict[str, dict[str, Any] | str]:
        if self._json_config_manager:
            return self._json_config_manager.get_mcp_deep_research_servers()
        # MCP not supported in INI config
        return {}

    def get_exa_api_key(self) -> str | None:
        if self._json_config_manager:
            return self._json_config_manager.get_exa_api_key()

        if self._ini_config_manager and "EXA" in self._ini_config_manager:
            return self._ini_config_manager["EXA"].get("api_key")
        return None

    def get_groq_api_key(self) -> str | None:
        if self._json_config_manager:
            return self._json_config_manager.get_groq_api_key()

        if self._ini_config_manager and "GROQ" in self._ini_config_manager:
            return self._ini_config_manager["GROQ"].get("api_key")
        return None

    def _load_ini_config(self) -> configparser.ConfigParser:
        config_path = get_legacy_config_path()
        config = configparser.ConfigParser()
        config.read(config_path)
        return config
