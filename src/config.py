import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file at the project root
# Adjust path if .env is elsewhere or structure changes
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.debug(f"Loaded environment variables from: {dotenv_path}")
else:
    logger.warning(f".env file not found at expected location: {dotenv_path}. Relying on system environment variables.")

# --- Spotify API Configuration ---
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://127.0.0.1:8080') # Default if not set

# --- Usernames ---
# Ensure these are set in your .env file or environment
EXPORT_USERNAME = os.getenv('EXPORT_USERNAME')
IMPORT_USERNAME = os.getenv('IMPORT_USERNAME')
ERASE_USERNAME = os.getenv('ERASE_USERNAME')

# --- Spotify API Scopes ---
# Added 'playlist-read-private' to ensure all playlists are fetched during export
SPOTIFY_SCOPE = (
    'playlist-read-private '      
    'playlist-modify-public '
    'playlist-modify-private '
    'user-library-read '
    'user-library-modify'
)

# --- File Paths & Patterns ---
# Use absolute path based on this config file's location
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__)) # Root is one level up from src
CACHE_DIR = PROJECT_ROOT # Store cache files in the root directory
DATA_FILE = os.path.join(PROJECT_ROOT, "spotify_data.json") # Default data file name in root

# --- Validation ---
def validate_config() -> bool:
    """Checks if essential configuration variables are set."""
    required_vars = {
        'CLIENT_ID': CLIENT_ID, 
        'CLIENT_SECRET': CLIENT_SECRET, 
        'EXPORT_USERNAME': EXPORT_USERNAME, 
        'IMPORT_USERNAME': IMPORT_USERNAME, 
        'ERASE_USERNAME': ERASE_USERNAME,
        'REDIRECT_URI': REDIRECT_URI
    }
    missing_vars = [name for name, value in required_vars.items() if not value]
    
    if missing_vars:
        logger.error(f"Missing required configuration: {', '.join(missing_vars)}")
        logger.error("Please ensure these are set in your .env file or environment variables.")
        return False
        
    logger.debug("Configuration validated successfully.")
    return True

# Perform validation when the module is loaded
IS_CONFIG_VALID = validate_config()