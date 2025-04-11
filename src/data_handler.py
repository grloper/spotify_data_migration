import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def save_data(data: Dict[str, Any], filepath: str):
    """Saves the provided data dictionary to a JSON file."""
    logger.debug(f"Attempting to save data to {filepath}")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully exported data to {filepath}")
    except IOError as e:
        logger.error(f"Error writing data to file {filepath}: {e}", exc_info=True)
        raise # Re-raise to indicate failure to the caller
    except TypeError as e:
        logger.error(f"Error serializing data to JSON for file {filepath}: {e}", exc_info=True)
        raise

def load_data(filepath: str) -> Optional[Dict[str, Any]]:
    """Loads data from a JSON file."""
    logger.debug(f"Attempting to load data from {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded data from {filepath}")
        
        # Basic validation
        if not isinstance(data, dict):
            logger.error(f"Invalid data format in {filepath}. Expected a dictionary, got {type(data)}.")
            return None
        if 'playlists' not in data or not isinstance(data['playlists'], list):
             logger.error(f"Invalid data format in {filepath}. Missing or invalid 'playlists' key (should be a list).")
             return None
        if 'liked_songs' not in data or not isinstance(data['liked_songs'], list):
             logger.error(f"Invalid data format in {filepath}. Missing or invalid 'liked_songs' key (should be a list).")
             return None
             
        return data
    except FileNotFoundError:
        logger.error(f"Data file not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from file {filepath}: {e}", exc_info=True)
        return None
    except IOError as e:
        logger.error(f"Error reading data file {filepath}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading data from {filepath}: {e}", exc_info=True)
        return None