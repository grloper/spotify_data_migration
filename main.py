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
from src.ui.spotify_app_window import SpotifyMigrationApp
from src.ui.logger import setup_logger

def main():
    # Set up logging
    logger = setup_logger()
    logger.info("Starting Spotify Data Migration App")
    
    # Create and start the application
    app = QApplication(sys.argv)
    window = SpotifyMigrationApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
