import argparse
import logging
import time
import sys

# Import modules from the 'src' package using relative imports
from . import config
from .logger import setup_logging
from .spotify_manager import SpotifyManager
from .data_handler import save_data, load_data

# Setup module-level logger
logger = logging.getLogger(__name__)

def run_export(manager: SpotifyManager, data_file: str):
    """Handles the export process."""
    start_time = time.time()
    logger.info("Starting Spotify data export...")

    playlists_raw = manager.get_all_playlists()
    if playlists_raw is None: # Check if fetching failed
        logger.error("Failed to fetch playlists. Aborting export.")
        return False

    playlist_data = []
    for p in playlists_raw:
        logger.info(f"Fetching tracks for playlist: {p.get('name', 'Unnamed Playlist')} (ID: {p['id']})")
        tracks = manager.get_playlist_tracks(p['id'])
        if tracks is None: # Check if fetching tracks failed
             logger.warning(f"Failed to fetch tracks for playlist {p.get('name', 'Unnamed Playlist')}. Skipping tracks for this playlist.")
             tracks = [] # Store empty list for this playlist if tracks couldn't be fetched

        playlist_data.append({
            'id': p['id'],
            'name': p.get('name', 'Unnamed Playlist'), # Handle potential missing name
            'public': p.get('public', False), # Default to False if missing
            'description': p.get('description', ''), # Include description
            'tracks': tracks
        })

    liked_songs = manager.get_liked_songs()
    if liked_songs is None: # Check if fetching failed
        logger.error("Failed to fetch liked songs. Aborting export.")
        return False

    export_content = {'playlists': playlist_data, 'liked_songs': liked_songs}
    
    try:
        save_data(export_content, data_file)
        logger.info(f"Export completed successfully in {time.time() - start_time:.2f} seconds.")
        return True
    except Exception:
        logger.error("Failed to save exported data to file.")
        return False


def run_import(manager: SpotifyManager, data_file: str):
    """Handles the import process."""
    start_time = time.time()
    logger.info("Starting Spotify data import...")

    data_to_import = load_data(data_file)
    if not data_to_import:
        logger.error(f"Could not load data from {data_file}. Aborting import.")
        return False

    # Import Liked Songs first
    if 'liked_songs' in data_to_import:
        manager.add_tracks_to_library(data_to_import['liked_songs'])
    else:
        logger.warning("No 'liked_songs' key found in data file. Skipping liked songs import.")

    # Import Playlists
    if 'playlists' in data_to_import:
        logger.info(f"Importing {len(data_to_import['playlists'])} playlists...")
        for i, playlist in enumerate(data_to_import['playlists'], 1):
            logger.info(f"--- Processing playlist {i}/{len(data_to_import['playlists'])} ---")
            playlist_name = playlist.get('name', f'Imported Playlist {i}')
            is_public = playlist.get('public', False) # Default to private if missing
            track_uris = playlist.get('tracks', [])

            if not isinstance(track_uris, list):
                 logger.warning(f"Skipping playlist '{playlist_name}' due to invalid 'tracks' format (expected list).")
                 continue # Skip this playlist

            manager.create_playlist_and_add_tracks(playlist_name, is_public, track_uris)
            # Add a small delay to potentially avoid hitting rate limits too quickly
            time.sleep(0.5) 
    else:
        logger.warning("No 'playlists' key found in data file. Skipping playlist import.")

    logger.info(f"Import completed in {time.time() - start_time:.2f} seconds.")
    return True # Indicate completion, even if some items failed


def run_erase(manager: SpotifyManager):
    """Handles the erase process."""
    start_time = time.time()
    logger.warning("Starting Spotify data erasure. This action is irreversible!")
    
    # Confirm action - Basic console confirmation
    confirm = input("Are you sure you want to delete ALL playlists and liked songs for this user? (yes/no): ").lower()
    if confirm != 'yes':
        logger.info("Erasure cancelled by user.")
        return False

    # Erase Playlists
    logger.info("Fetching playlists to delete...")
    playlists = manager.get_all_playlists()
    if playlists is None:
        logger.error("Failed to fetch playlists. Cannot proceed with playlist deletion.")
    elif playlists:
        logger.info(f"Found {len(playlists)} playlists to delete.")
        for i, playlist in enumerate(playlists, 1):
            playlist_name = playlist.get('name', 'Unnamed Playlist')
            playlist_id = playlist['id']
            logger.warning(f"Deleting playlist {i}/{len(playlists)}: '{playlist_name}' (ID: {playlist_id})")
            manager.unfollow_playlist(playlist_id)
            time.sleep(0.2) # Small delay
        logger.info("Finished deleting playlists.")
    else:
        logger.info("No playlists found to delete.")


    # Erase Liked Songs
    logger.info("Fetching liked songs to delete...")
    liked_songs = manager.get_liked_songs()
    if liked_songs is None:
        logger.error("Failed to fetch liked songs. Cannot proceed with liked songs deletion.")
    elif liked_songs:
        manager.remove_tracks_from_library(liked_songs)
        logger.info("Finished deleting liked songs.")
    else:
        logger.info("No liked songs found to delete.")


    logger.info(f"Erasure process completed in {time.time() - start_time:.2f} seconds.")
    return True


def main():
    """Main function to parse arguments and run the selected action."""
    parser = argparse.ArgumentParser(description="Manage Spotify playlists and liked songs.")
    
    # Action group - only one action can be chosen
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--export', action='store_true', help='Export data from Spotify account specified by EXPORT_USERNAME.')
    action_group.add_argument('--import-data', action='store_true', help='Import data to Spotify account specified by IMPORT_USERNAME.')
    action_group.add_argument('--erase', action='store_true', help='Delete all playlists and liked songs from account specified by ERASE_USERNAME.')

    # Options
    parser.add_argument('--debug', action='store_true', help='Enable detailed debug logging.')
    parser.add_argument('--clean-cache', action='store_true', help='Delete OAuth cache file before authenticating.')
    parser.add_argument('--data-file', type=str, default=config.DATA_FILE, help=f'Specify the JSON file for export/import (default: {config.DATA_FILE})')

    args = parser.parse_args()

    # --- Setup Logging ---
    setup_logging(debug=args.debug)
    logger.info("Logging configured.")
    
    # --- Validate Configuration ---
    if not config.IS_CONFIG_VALID:
        logger.critical("Configuration is invalid. Please check .env file or environment variables. Exiting.")
        sys.exit(1) # Exit if config is bad

    # --- Determine Action and Username ---
    username = None
    action_func = None
    if args.export:
        username = config.EXPORT_USERNAME
        action_func = run_export
        logger.info(f"Action: Export | User: {username}")
    elif args.import_data:
        username = config.IMPORT_USERNAME
        action_func = run_import
        logger.info(f"Action: Import | User: {username}")
    elif args.erase:
        username = config.ERASE_USERNAME
        action_func = run_erase
        logger.info(f"Action: Erase | User: {username}")

    if not username:
         logger.critical("Could not determine Spotify username for the selected action. Check EXPORT/IMPORT/ERASE_USERNAME in config. Exiting.")
         sys.exit(1)

    # --- Initialize Spotify Manager ---
    manager = SpotifyManager(
        username=username,
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        scope=config.SPOTIFY_SCOPE
    )

    # --- Authenticate ---
    logger.info(f"Attempting to authenticate user: {username}")
    if not manager.authenticate(clean_cache=args.clean_cache):
        logger.critical("Authentication failed. Please check logs for details. Exiting.")
        sys.exit(1)

    # --- Execute Action ---
    success = False
    try:
        if action_func == run_export:
            success = action_func(manager, args.data_file)
        elif action_func == run_import:
            success = action_func(manager, args.data_file)
        elif action_func == run_erase:
             success = action_func(manager)
             
    except Exception as e:
        # Catch any unexpected errors during the main action execution
        logger.critical(f"An unexpected error occurred during the '{action_func.__name__}' process: {e}", exc_info=True)
        sys.exit(1) # Exit on critical unexpected error

    if success:
        logger.info("Operation finished.")
        sys.exit(0) # Success exit code
    else:
        logger.error("Operation failed. Please review logs.")
        sys.exit(1) # Failure exit code


if __name__ == '__main__':
    main()