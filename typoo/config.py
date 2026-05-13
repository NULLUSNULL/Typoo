"""
Global configuration for Typoo application.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Centralized configuration for the application."""
    
    # Application metadata
    APP_NAME = "Typoo"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "NULLUSNULL"
    APP_LICENSE = "MIT"
    
    # Paths
    ROOT_DIR = Path(__file__).parent.parent
    ASSETS_DIR = ROOT_DIR / "typoo" / "assets"
    ICONS_DIR = ASSETS_DIR / "icons"
    THEMES_DIR = ASSETS_DIR / "themes"
    DATA_DIR = Path.home() / ".typoo"
    
    # File extensions
    MARKDOWN_EXT = ".md"
    PROJECT_EXT = ".typoo"
    METADATA_EXT = ".typoo.json"
    
    # Editor settings
    EDITOR_FONT_SIZE = 12
    EDITOR_FONT_FAMILY = "Consolas" if os.name == "nt" else "Monospace"
    EDITOR_WRAP = True
    TAB_SIZE = 4
    
    # UI settings
    THEME_DARK = "dark"
    THEME_LIGHT = "light"
    DEFAULT_THEME = THEME_DARK
    
    # Splitter settings
    MAX_PANELS = 3
    DEFAULT_PANEL_WIDTHS = [200, 600, 200]
    
    # Autosave settings
    AUTOSAVE_ENABLED = True
    AUTOSAVE_INTERVAL = 30  # seconds
    
    # Backup settings
    BACKUP_ENABLED = True
    BACKUP_INTERVAL = 300  # seconds
    MAX_BACKUPS = 5
    
    # UI window settings
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    
    # Search settings
    MAX_SEARCH_RESULTS = 1000
    ENABLE_REGEX_SEARCH = True
    
    @classmethod
    def ensure_data_dir(cls) -> Path:
        """Ensure data directory exists."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return cls.DATA_DIR
    
    @classmethod
    def get_asset_path(cls, asset_type: str, filename: str) -> Optional[Path]:
        """Get path to asset file."""
        if asset_type == "icon":
            path = cls.ICONS_DIR / filename
        elif asset_type == "theme":
            path = cls.THEMES_DIR / filename
        else:
            return None
        
        return path if path.exists() else None
