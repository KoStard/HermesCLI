#!/usr/bin/env python
"""
Script to debug config loading and key extraction.

Usage:
    uv run python scripts/debug_config.py

This script will:
1. Load both INI and JSON configs (if available)
2. Print the loaded config values
3. Extract key settings that might be causing issues
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hermes.config_manager import ConfigManager
from hermes.json_config_manager import JsonConfigManager
from hermes.utils.config_utils import get_json_config_path, get_legacy_config_path


def main():
    """Debug config loading and extraction."""
    print("=== Hermes Config Debugger ===\n")

    # Check file presence
    json_path = get_json_config_path()
    ini_path = get_legacy_config_path()

    print(f"JSON config path: {json_path} (exists: {json_path.exists()})")
    print(f"INI config path: {ini_path} (exists: {ini_path.exists()})")
    print()

    # Try loading with config manager
    print("Loading with primary ConfigManager:")
    try:
        config_manager = ConfigManager()
        model_info = config_manager.get_default_model_info_string()
        print(f"  Default model: {model_info}")

        overrides = config_manager.get_command_status_overrides()
        print(f"  Command overrides: {overrides}")
        print("  Config type:", type(config_manager.get_config()).__name__)
        print()
    except Exception as e:
        print(f"  ERROR loading with ConfigManager: {e}")
        print()

    # Try loading JSON directly
    if json_path.exists():
        print(f"Direct JSON config testing ({json_path}):")
        try:
            json_manager = JsonConfigManager()

            # Get and print the full config (formatted)
            full_config = json_manager.get_config()
            print("  Full config content:")
            print(json.dumps(full_config, indent=2))
            print()

            # Test model extraction
            model_info = json_manager.get_default_model_info_string()
            print(f"  Default model: {model_info}")

            # Check both locations for the model setting
            top_level_model = full_config.get("model")
            base_model = full_config.get("base", {}).get("model") if isinstance(full_config.get("base"), dict) else None
            print(f"  Model in top level: {top_level_model}")
            print(f"  Model in base section: {base_model}")
            print()
        except Exception as e:
            print(f"  ERROR loading JSON config: {e}")
            print()

    print("Config debugging complete.")


if __name__ == "__main__":
    main()
