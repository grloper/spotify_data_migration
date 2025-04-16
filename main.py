#!/usr/bin/env python3
"""
Spotify Data Migration App
Main entry point for the application
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from gui import SpotifyMigrationApp  # Import from root-level gui.py instead of src.ui.gui
from src.ui.logger import setup_logger

if __name__ == "__main__":
    # Set up logging
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting Spotify Data Migration App")
    
    # Create and start the application
    app = QApplication(sys.argv)
    window = SpotifyMigrationApp()
    window.show()
    sys.exit(app.exec_())
