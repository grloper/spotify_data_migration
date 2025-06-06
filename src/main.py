import logging
import sys
from .logger import setup_logging
from .gui import start_gui

def main():
    """Main function to launch GUI app."""
    # Set up logging
    setup_logging(debug=False)
    logger = logging.getLogger(__name__)
    logger.info("Starting Spotify Data Migration GUI")
    
    # Launch the GUI directly
    start_gui()

if __name__ == '__main__':
    main()