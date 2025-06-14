import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Any

from appdirs import user_config_dir


def _get_config_root_dir() -> Path:
    """Determines the root directory for Hermes configuration files based on OS.

    - Linux & macOS: Uses ~/.config/hermes/
    - Windows: Uses the standard AppData directory (%APPDATA%\\hermes\\)
    """
    if sys.platform in ["linux", "darwin"]:  # darwin is macOS
        # Use the desired path for Linux and macOS
        return Path.home() / ".config" / "hermes"
    if sys.platform == "win32":
        # Use standard Windows path via appdirs (without appauthor)
        # Gives C:\Users\<User>\AppData\Roaming\hermes\
        return Path(user_config_dir(appname="hermes", appauthor=False))
    # Fallback for other potential OS - default to Unix-like style
    print(f"Warning: Unsupported platform '{sys.platform}'. Defaulting config path to ~/.config/hermes/")
    return Path.home() / ".config" / "hermes"


def get_legacy_config_path() -> Path:
    """Returns the full path to the config.ini file."""
    return _get_config_root_dir() / "config.ini"


def get_json_config_path() -> Path:
    """Returns the full path to the config.json file."""
    return _get_config_root_dir() / "config.json"


def get_extensions_dir_path() -> Path:
    """Returns the full path to the extensions directory."""
    return _get_config_root_dir() / "extensions"


def convert_ini_to_json(ini_config: ConfigParser) -> dict[str, Any]:
    """Convert ConfigParser (INI) object to a JSON-compatible dictionary.

    This is a utility function for migrating from INI config to JSON config.

    Args:
        ini_config: The ConfigParser object loaded from an INI file.

    Returns:
        A dictionary with the same structure as the JSON config file.
    """
    json_config = {}

    for section in ini_config.sections():
        json_config[section.lower()] = {}
        for key, value in ini_config[section].items():
            _add_value_to_json(json_config, section.lower(), key, value)

    return json_config

def _add_value_to_json(json_config: dict, section_name: str, key: str, value: Any):
    # Try to parse to appropriate types
    if value.lower() == "true":
        json_config[section_name][key] = True
    elif value.lower() == "false":
        json_config[section_name][key] = False
    elif value.isdigit():
        json_config[section_name][key] = int(value)
    elif "," in value and "[" not in value and "{" not in value:
        # Simple comma-separated list
        json_config[section_name][key] = [item.strip() for item in value.split(",")]
    else:
        json_config[section_name][key] = value


def extract_config_section(config: ConfigParser | dict[str, Any], section: str) -> dict[str, Any]:
    """Extract a section from either ConfigParser or a dict-based config.

    Args:
        config: Either a ConfigParser object or a dictionary.
        section: The section name to extract.

    Returns:
        A dictionary containing the configuration for the specified section.

    Raises:
        ValueError: If the section doesn't exist in the config.
    """
    if isinstance(config, ConfigParser):
        # Handle ConfigParser
        if section not in config.sections():
            raise ValueError(
                f"Config section {section} is not found. Please double check it and specify "
                "it in the config file ~/.config/hermes/config.ini. You might need to specify the api_key there.",
            )
        # Convert ConfigParser section to dict
        return {key: value for key, value in config[section].items()}

    # Handle dictionary-based config
    if section.lower() not in config:
        raise ValueError(
            f"Config section {section} is not found. Please double check it and specify "
            "it in the config file ~/.config/hermes/config.json. You might need to specify the api_key there.",
        )
    # Get the section from the dictionary (case insensitive)
    section_key = next(k for k in config if k.lower() == section.lower())
    section_data = config[section_key]
    # If the section is already a dictionary, return it
    if isinstance(section_data, dict):
        return section_data
    # If it's a simple value (like an API key string), wrap it in a dict
    return {"api_key": section_data} if isinstance(section_data, str) else {"value": section_data}
