"""
Typoo - Professional Writing Suite
A cross-platform application for writing novels and literary projects.

Author: NULLUSNULL
License: MIT
"""

__version__ = "1.0.0"
__author__ = "NULLUSNULL"
__license__ = "MIT"

from typoo.config import Config
from typoo.logger import Logger

# Initialize configuration and logging
config = Config()
logger = Logger.setup()

__all__ = ["config", "logger", "__version__", "__author__", "__license__"]
