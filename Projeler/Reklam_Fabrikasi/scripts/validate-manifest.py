#!/usr/bin/env python3
"""Validate the reklam-fabrikasi plugin manifest against Claude Code's documented
schema before release.

This script catches the class of bug that shipped in v1.3.4, where an
unrecognized userConfig key ("placeholder") slipped past every prior pass
because jq only checks JSON syntax, not Claude Code's plugin manifest schema.

The allowed key lists are pulled from Anthropic's published plugin reference:
https://code.claude.com/docs/en/plugins-reference

Run from the plugin root:
    python3 scripts/validate-manifest.py

Exits 0 on success, 1 on any schema or cross-file consistency failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# Allowed top-level keys in .claude-plugin/plugin.json.
# Source: https://code.claude.com/docs/en/plugins-reference
# Sections "Required fields", "Metadata fields", "Component path fields".
ALLOWED_PLUGIN_TOP_LEVEL_KEYS: set[str] = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "skills",
    "commands",
    "agents",
    "hooks",
    "mcpServers",
    "outputStyles",
    "themes",
    "lspServers",
    "monitors",
    "userConfig",
    "channels",
    "dependencies",
}

# Required top-level keys for plugin.json.
# Source: same doc, "Required fields" table. Only "name" is strictly required.
# We additionally require "version" because this plugin's release process is
# version-pinned and version mismatch is the second class of bug we are
# guarding against.
REQUIRED_PLUGIN_TOP_LEVEL_KEYS: set[str] = {"name", "version"}


# Allowed keys for a single entry inside plugin.json's userConfig object.
# Source: https://code.claude.com/docs/en/plugins-reference
# Section "User configuration", the per-option fields table.
ALLOWED_USER_CONFIG_ENTRY_KEYS: set[str] = {
    "type",
    "title",
    "description",
    "sensitive",
    "required",
    "default",
    "multiple",
    "min",
    "max",
}

# Required keys per the same doc table.
REQUIRED_USER_CONFIG_ENTRY_KEYS: set[str] = {"type", "title", "description"}

# Valid values for the "type" field per the same doc table.
ALLOWED_USER_CONFIG_TYPES: set[str] = {
    "string",
    "number",
    "boolean",
    "directory",
    "file",
}


# Required top-level keys for marketplace.json.
# Source: https://code.claude.com/docs/en/plugin-marketplaces
# Section "Marketplace schema", "Required fields" table.
REQUIRED_MARKETPLACE_TOP_LEVEL_KEYS: set[str] = {"name", "owner", "plugins"}

# Required keys for each entry in marketplace.json's plugins array.
# The doc lists "name" and "source" as strictly required, but this plugin's
# release process pins versions, so we additionally require "version" to
# guarantee marketplace and plugin manifests stay in lockstep.
REQUIRED_MARKETPLACE_PLUGIN_ENTRY_KEYS: set[str] = {"name", "version", "source"}


def fail(message: str) -> None:
    """Print an error and exit 1."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"{path}: file does not exist")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON, {exc}")
    return None  # unreachable, fail() exits


def validate_plugin_top_level(plugin: dict[str, Any], path: Path) -> None:
    if not isinstance(plugin, dict):
        fail(f"{path}: top level must be a JSON object")

    for required in sorted(REQUIRED_PLUGIN_TOP_LEVEL_KEYS):
        if required not in plugin:
            fail(f"{path}: missing required field '{required}'")

    unknown = set(plugin.keys()) - ALLOWED_PLUGIN_TOP_LEVEL_KEYS
    if unknown:
        valid = ", ".join(sorted(ALLOWED_PLUGIN_TOP_LEVEL_KEYS))
        for key in sorted(unknown):
            print(
                f"ERROR: {path}: unrecognized top-level key '{key}'. "
                f"Valid keys: {valid}.",
                file=sys.stderr,
            )
        sys.exit(1)

    name = plugin.get("name")
    if not isinstance(name, str) or not name.strip():
        fail(f"{path}: 'name' must be a non-empty string")

    version = plugin.get("version")
    if not isinstance(version, str) or not version.strip():
        fail(f"{path}: 'version' must be a non-empty string")


def validate_user_config(plugin: dict[str, Any], path: Path) -> None:
    user_config = plugin.get("userConfig")
    if user_config is None:
        return
    if not isinstance(user_config, dict):
        fail(f"{path}: 'userConfig' must be a JSON object")

    valid_keys_label = ", ".join(sorted(ALLOWED_USER_CONFIG_ENTRY_KEYS))
    failures = 0

    for entry_name, entry in user_config.items():
        if not isinstance(entry, dict):
            print(
                f"ERROR: {path}: userConfig.{entry_name} must be a JSON object",
                file=sys.stderr,
            )
            failures += 1
            continue

        unknown = set(entry.keys()) - ALLOWED_USER_CONFIG_ENTRY_KEYS
        for key in sorted(unknown):
            print(
                f"ERROR: {path}: userConfig.{entry_name}: "
                f"Unrecognized key '{key}'. Valid keys: {valid_keys_label}.",
                file=sys.stderr,
            )
            failures += 1

        missing = REQUIRED_USER_CONFIG_ENTRY_KEYS - set(entry.keys())
        for key in sorted(missing):
            print(
                f"ERROR: {path}: userConfig.{entry_name}: "
                f"missing required key '{key}'",
                file=sys.stderr,
            )
            failures += 1

        type_value = entry.get("type")
        if type_value is not None and type_value not in ALLOWED_USER_CONFIG_TYPES:
            valid_types_label = ", ".join(sorted(ALLOWED_USER_CONFIG_TYPES))
            print(
                f"ERROR: {path}: userConfig.{entry_name}: "
                f"invalid type '{type_value}'. Valid types: {valid_types_label}.",
                file=sys.stderr,
            )
            failures += 1

    if failures > 0:
        sys.exit(1)


def validate_marketplace(
    marketplace: Any, path: Path, plugin_name: str, plugin_version: str
) -> None:
    if not isinstance(marketplace, dict):
        fail(f"{path}: top level must be a JSON object")

    for required in sorted(REQUIRED_MARKETPLACE_TOP_LEVEL_KEYS):
        if required not in marketplace:
            fail(f"{path}: missing required field '{required}'")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail(f"{path}: 'plugins' must be a non-empty array")

    matching = [
        entry for entry in plugins
        if isinstance(entry, dict) and entry.get("name") == plugin_name
    ]
    if not matching:
        fail(
            f"{path}: no plugins entry with name '{plugin_name}' to match "
            f"plugin.json. Found names: "
            f"{[e.get('name') for e in plugins if isinstance(e, dict)]}"
        )

    failures = 0
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            print(
                f"ERROR: {path}: plugins[{index}] must be a JSON object",
                file=sys.stderr,
            )
            failures += 1
            continue
        for required in sorted(REQUIRED_MARKETPLACE_PLUGIN_ENTRY_KEYS):
            if required not in entry:
                label = entry.get("name", f"index {index}")
                print(
                    f"ERROR: {path}: plugins entry '{label}' is missing "
                    f"required field '{required}'",
                    file=sys.stderr,
                )
                failures += 1

    if failures > 0:
        sys.exit(1)

    matched_entry = matching[0]
    marketplace_version = matched_entry.get("version")
    if marketplace_version != plugin_version:
        fail(
            f"version mismatch: .claude-plugin/plugin.json declares "
            f"'{plugin_version}' but {path} plugins entry '{plugin_name}' "
            f"declares '{marketplace_version}'"
        )


def validate_package_json(
    path: Path, plugin_name: str, plugin_version: str
) -> None:
    package = load_json(path)
    if not isinstance(package, dict):
        fail(f"{path}: top level must be a JSON object")

    package_name = package.get("name")
    if package_name != plugin_name:
        fail(
            f"name mismatch: .claude-plugin/plugin.json declares "
            f"'{plugin_name}' but {path} declares '{package_name}'"
        )

    package_version = package.get("version")
    if package_version != plugin_version:
        fail(
            f"version mismatch: .claude-plugin/plugin.json declares "
            f"'{plugin_version}' but {path} declares '{package_version}'"
        )


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    plugin_path = repo_root / ".claude-plugin" / "plugin.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    package_path = repo_root / "package.json"

    plugin = load_json(plugin_path)
    validate_plugin_top_level(plugin, plugin_path)
    validate_user_config(plugin, plugin_path)

    plugin_name = plugin["name"]
    plugin_version = plugin["version"]

    marketplace = load_json(marketplace_path)
    validate_marketplace(marketplace, marketplace_path, plugin_name, plugin_version)

    validate_package_json(package_path, plugin_name, plugin_version)

    print(f"Manifest valid. Plugin version: {plugin_version}")
    sys.exit(0)


if __name__ == "__main__":
    main()
