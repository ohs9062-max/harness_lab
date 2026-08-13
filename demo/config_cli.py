#!/usr/bin/env python3
"""Print a value from the JSON configuration file next to this script."""

import json
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("config.json")


def main() -> int:
    if len(sys.argv) != 2:
        print("ERROR: provide exactly one key", file=sys.stderr)
        return 2

    try:
        with CONFIG_PATH.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: could not read configuration: {error}", file=sys.stderr)
        return 1

    if not isinstance(config, dict):
        print("ERROR: configuration root must be a JSON object", file=sys.stderr)
        return 1

    key = sys.argv[1]
    if key not in config:
        print(f"ERROR: key '{key}' not found", file=sys.stderr)
        return 1

    print(config[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
