#!/usr/bin/env python3
"""
Typoo Launcher - Platform-independent launcher script
"""

import sys
import os
from pathlib import Path

def main():
    """Launch Typoo application."""
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Check Python version
    if sys.version_info < (3, 9):
        print(f"Error: Python 3.9+ required. Current version: {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    
    try:
        # Import and run
        from typoo.ui.main_window import MainWindow
        from typoo.config import Config
        from typoo.logger import Logger
        from PySide6.QtWidgets import QApplication
        
        # Setup logging
        log_file = Config.ensure_data_dir() / "typoo.log"
        logger = Logger.setup(log_file=log_file)
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info(f"Typoo v{Config.APP_VERSION} launched")
        
        # Run event loop
        sys.exit(app.exec())
    
    except ImportError as e:
        print(f"Error: Missing required package: {str(e)}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
