import sys
from pathlib import Path

from appdirs import user_config_dir


def _get_config_root_dir() -> Path:
    """
    Determines the root directory for Hermes configuration files based on OS.

    - Linux & macOS: Uses ~/.config/hermes/
    - Windows: Uses the standard AppData directory (%APPDATA%\\hermes\\)
    """
    if sys.platform in ["linux", "darwin"]:  # darwin is macOS
        # Use the desired path for Linux and macOS
        return Path.home() / ".config" / "hermes"
    elif sys.platform == "win32":
        # Use standard Windows path via appdirs (without appauthor)
        # Gives C:\Users\<User>\AppData\Roaming\hermes\
        return Path(user_config_dir(appname="hermes", appauthor=False))
    else:
        # Fallback for other potential OS - default to Unix-like style
        print(f"Warning: Unsupported platform '{sys.platform}'. Defaulting config path to ~/.config/hermes/")
        return Path.home() / ".config" / "hermes"


def get_config_path() -> Path:
    """Returns the full path to the config.ini file."""
    return _get_config_root_dir() / "config.ini"


def get_extensions_dir_path() -> Path:
    """Returns the full path to the extensions directory."""
    return _get_config_root_dir() / "extensions"
