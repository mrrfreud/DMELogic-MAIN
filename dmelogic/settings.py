"""
settings.py — Load and save persistent settings.
"""

import json
import os
from typing import Optional
from .config import SETTINGS_FILE, _default_db_folder, debug_log


# Global in-memory cache to avoid repeated disk reads
_SETTINGS_CACHE: Optional[dict] = None


def load_settings(create_if_missing: bool = False) -> dict:
    """
    Load settings.json.
    
    Args:
        create_if_missing: If True, create default settings if file doesn't exist.
                          If False (default), return empty dict if file doesn't exist.
                          The First-Run Wizard should handle initial setup.
    
    Cached in memory after first read for performance.
    """
    global _SETTINGS_CACHE
    
    # Return cached settings if available
    if _SETTINGS_CACHE is not None:
        return _SETTINGS_CACHE
    
    # Load from disk
    if not os.path.exists(SETTINGS_FILE):
        if create_if_missing:
            settings = {
                "db_folder": _default_db_folder(),
                "last_open_folder": "",
                "fee_schedule_path": "",
                "theme": "light"
            }
            save_settings(settings)
            return settings
        # Don't auto-create - let First-Run Wizard handle it
        return {}

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _SETTINGS_CACHE = data
            return data
    except Exception as e:
        debug_log(f"Failed to load settings.json: {e}")
        return {}


def save_settings(data: dict):
    """
    Safely write settings.json and update cache.
    """
    global _SETTINGS_CACHE
    
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # Update cache after successful write
        _SETTINGS_CACHE = data
    except Exception as e:
        debug_log(f"Failed to save settings.json: {e}")


def invalidate_settings_cache():
    """
    Clear the settings cache to force reload from disk.
    Useful for testing or when settings are modified externally.
    """
    global _SETTINGS_CACHE
    _SETTINGS_CACHE = None
