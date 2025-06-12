#!/usr/bin/env python
"""
Script to migrate from INI config format to JSON config format.

Usage:
    uv run python scripts/migrate_config.py

This script will:
1. Read the existing INI config file
2. Convert it to JSON format
3. Save it to the new JSON config file location
4. Create a backup of the original INI file
"""

import configparser
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hermes.utils.config_utils import (
    convert_ini_to_json,
    get_json_config_path,
    get_legacy_config_path,
)


def main():
    """Migrate from INI to JSON config format."""
    ini_path = get_legacy_config_path()
    json_path = get_json_config_path()

    # Check if INI file exists
    if not ini_path.exists():
        print(f"INI config file not found at {ini_path}")
        return

    # Load INI config
    print(f"Loading INI config from {ini_path}")
    config = configparser.ConfigParser()
    config.read(ini_path)

    # Convert to JSON
    json_config = convert_ini_to_json(config)

    # Create parent directory for JSON config if it doesn't exist
    json_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    print(f"Saving JSON config to {json_path}")
    with open(json_path, "w") as f:
        json.dump(json_config, f, indent=2)

    # Create backup of INI file
    backup_path = ini_path.with_suffix(".ini.bak")
    print(f"Creating backup of INI config at {backup_path}")
    ini_path.rename(backup_path)

    print("Migration complete!")
    print("You can now use the JSON config file.")
    print(f"A backup of your INI config is available at {backup_path}")


if __name__ == "__main__":
    main()
