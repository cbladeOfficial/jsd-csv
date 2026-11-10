"""
Configuration Management for JSD-CSV.
Allows saving, loading, editing, and merging user presets/parameters via JSON config files.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILES = ["config.json", "jsd-config.json"]

DEFAULT_CONFIG: Dict[str, Any] = {
    "url": "",
    "csv": "",
    "output": "./downloads",
    "mode": "all",
    "quality": "320",
    "source": "auto",
    "template": "{artist} - {title}",
    "lyrics": True,
    "cover": True,
    "cookies": None,
    "id3_version": 4,
}


def find_default_config() -> Optional[str]:
    """Finds an existing configuration file in the current working directory."""
    for filename in DEFAULT_CONFIG_FILES:
        if os.path.exists(filename) and os.path.isfile(filename):
            return os.path.abspath(filename)
    return None


def load_config(file_path: str) -> Dict[str, Any]:
    """
    Loads configuration dictionary from a JSON file.
    
    Args:
        file_path: Path to the JSON configuration file.
        
    Returns:
        Dictionary of loaded configuration options merged with default fallbacks.
    """
    clean_path = os.path.abspath(file_path.strip().strip("'\""))
    if not os.path.exists(clean_path):
        raise FileNotFoundError(f"Configuration file not found: {clean_path}")

    try:
        with open(clean_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse config file '{clean_path}': {e}")
        raise ValueError(f"Invalid JSON configuration file: {e}") from e

    merged = dict(DEFAULT_CONFIG)
    if isinstance(data, dict):
        for k, v in data.items():
            if k in DEFAULT_CONFIG and v is not None:
                merged[k] = v
            elif k in ("from_csv", "csv_input"):
                merged["csv"] = v
            elif k in ("id3v2_version", "id3"):
                try:
                    merged["id3_version"] = int(v)
                except (ValueError, TypeError):
                    pass

    return merged


def save_config(config_dict: Dict[str, Any], file_path: str = "config.json") -> str:
    """
    Saves a configuration dictionary to a cleanly formatted JSON file.
    
    Args:
        config_dict: Parameters to save.
        file_path: Destination file path (default: config.json).
        
    Returns:
        Absolute path to the saved configuration file.
    """
    clean_path = os.path.abspath(file_path.strip().strip("'\""))
    if not clean_path.lower().endswith(".json"):
        clean_path += ".json"

    parent_dir = os.path.dirname(clean_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    to_save = {
        "url": str(config_dict.get("url") or "").strip(),
        "csv": str(config_dict.get("csv") or config_dict.get("from_csv") or "").strip(),
        "output": str(config_dict.get("output") or "./downloads").strip(),
        "mode": str(config_dict.get("mode") or "all").strip().lower(),
        "quality": str(config_dict.get("quality") or "320").strip(),
        "source": str(config_dict.get("source") or "auto").strip().lower(),
        "template": str(config_dict.get("template") or "{artist} - {title}").strip(),
        "lyrics": bool(config_dict.get("lyrics", True)),
        "cover": bool(config_dict.get("cover", True)),
        "cookies": config_dict.get("cookies") or None,
        "id3_version": int(config_dict.get("id3_version", 4)),
    }

    try:
        with open(clean_path, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4)
        logger.info(f"Saved configuration profile to: {clean_path}")
        return clean_path
    except Exception as e:
        logger.error(f"Failed to write config file '{clean_path}': {e}")
        raise
