"""
theme_manager.py — Centralized theme management for DMELogic
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QApplication

from dmelogic.paths import get_assets_dir, get_theme_dir

logger = logging.getLogger("theme")


class ThemeManager:
    """Manages application theme switching between light and dark modes."""
    
    @staticmethod
    def apply_theme(app: QApplication, theme_name: str) -> None:
        """
        Apply a theme to the application.
        
        Args:
            app: QApplication instance
            theme_name: "light" for light mode or "dark" for dark mode
        """
        if theme_name == "dark":
            qss_path = get_theme_dir() / "dark.qss"
        else:
            # Use proper light theme
            qss_path = get_theme_dir() / "light.qss"

        logger.info(f"[ThemeManager] Applying theme '{theme_name}' from {qss_path}")

        if not qss_path.exists():
            logger.warning(f"[ThemeManager] Theme file not found: {qss_path}")
            return

        try:
            with qss_path.open("r", encoding="utf-8") as f:
                qss = f.read()
            app.setStyleSheet(qss)
            logger.info(f"[ThemeManager] Theme '{theme_name}' applied successfully ({len(qss)} chars).")
        except Exception:
            logger.exception(f"[ThemeManager] Failed to apply theme '{theme_name}'")
