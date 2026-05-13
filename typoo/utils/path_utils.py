"""
Path utilities for cross-platform compatibility.
"""

from pathlib import Path
from typing import Optional


class PathUtils:
    """Utilities for path handling."""
    
    @staticmethod
    def get_relative_path(file_path: Path, base_path: Path) -> str:
        """Get relative path from base to file."""
        try:
            return str(file_path.relative_to(base_path))
        except ValueError:
            return str(file_path)
    
    @staticmethod
    def ensure_unique_path(path: Path) -> Path:
        """Ensure path is unique by appending counter if needed."""
        if not path.exists():
            return path
        
        counter = 1
        while True:
            new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Convert string to safe filename."""
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename.strip()
