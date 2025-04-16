#!/usr/bin/env python
"""
Entry point for Spotify Data Migration Tool
This file uses absolute imports to avoid package issues when compiled
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the GUI module using absolute imports
from src.gui import start_gui

if __name__ == "__main__":
    # Launch the GUI directly
    start_gui()
