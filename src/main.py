import argparse
import logging
import time
import sys
import re
from typing import List, Dict, Any, Optional

# Import modules from the 'src' package using relative imports
from . import config
from .logger import setup_logging
from .spotify_manager import SpotifyManager
from .data_handler import save_data, load_data

# Setup module-level logger
logger = logging.getLogger(__name__)

def select_playlists(playlists: List[Dict[str, Any]], interactive: bool = True) -> List[Dict[str, Any]]:
    """
    Allow the user to select specific playlists from the full list.
    
    Args:
        playlists: List of playlist objects
        interactive: Whether to prompt user for selection
        
    Returns:
        List of selected playlist objects
    """
    if not interactive or not playlists:
        return playlists
    
    # Column widths
    idx_width = 4
    name_width = 40
    tracks_width = 12
    public_width = 6
    
    # Display playlists with numbers
    print("\nAvailable Playlists:")
    print("-" * (idx_width + name_width + tracks_width + public_width))
    
    # Format the header with proper spacing
    print(f"{'#':<{idx_width}}{'Playlist Name':<{name_width}}{'Track Count':<{tracks_width}}{'Public':<{public_width}}")
    print("-" * (idx_width + name_width + tracks_width + public_width))
    
    for i, playlist in enumerate(playlists, 1):
        name = playlist.get('name', 'Unnamed Playlist')
        
        # Truncate long names and add ellipsis if needed
        if len(name) > name_width - 3:
            name = name[:name_width - 3] + "..."
            
        track_count = len(playlist.get('tracks', [])) if 'tracks' in playlist else '?'
        is_public = "Yes" if playlist.get('public', False) else "No"
        
        # Print with consistent spacing
        print(f"{i:<{idx_width}}{name:<{name_width}}{track_count:<{tracks_width}}{is_public:<{public_width}}")
    
    print("\nSelection options:")
    print("- Enter numbers separated by commas (e.g., '1,3,5')")
    print("- Enter a range (e.g., '1-5')")
    print("- Enter 'all' to select all playlists")
    print("- Enter 'public' to select only public playlists")
    print("- Enter 'private' to select only private playlists")
    print("- Enter 'q' or press Ctrl+C to cancel")
    
    selected_playlists = []
    while not selected_playlists:
        try:
            selection = input("\nSelect playlists: ").strip().lower()
            
            if selection == 'q':
                logger.info("Selection cancelled by user.")
                return []
                
            if selection == 'all':
                return playlists
                
            if selection == 'public':
                return [p for p in playlists if p.get('public', False)]
                
            if selection == 'private':
                return [p for p in playlists if not p.get('public', False)]
            
            # Process comma-separated values and ranges
            indices = set()
            for part in selection.split(','):
                part = part.strip()
                if not part:
                    continue
                    
                # Check for range pattern (e.g., 1-5)
                range_match = re.match(r'^(\d+)-(\d+)$', part)
                if range_match:
                    start, end = int(range_match.group(1)), int(range_match.group(2))
                    if 1 <= start <= len(playlists) and 1 <= end <= len(playlists):
                        indices.update(range(start, end + 1))
                    else:
                        print(f"Range {start}-{end} out of bounds (1-{len(playlists)})")
                        continue
                # Check for single number
                elif part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(playlists):
                        indices.add(idx)
                    else:
                        print(f"Number {idx} out of bounds (1-{len(playlists)})")
                else:
                    print(f"Invalid input: '{part}'")
            
            # Convert 1-based indices to 0-based for list access
            selected_playlists = [playlists[i-1] for i in sorted(indices)]
            
            if not selected_playlists:
                print("No valid playlists selected. Please try again.")
            else:
                print(f"\nSelected {len(selected_playlists)} playlists:")
                for p in selected_playlists:
                    print(f"- {p.get('name', 'Unnamed Playlist')}")
                
                confirm = input("\nConfirm selection? (y/n): ").lower().strip()
                if confirm != 'y':
                    selected_playlists = []
                    print("Selection cancelled. Please try again.")
                
        except KeyboardInterrupt:
            logger.info("Selection cancelled by keyboard interrupt.")
            return []
        except Exception as e:
            logger.error(f"Error during playlist selection: {e}")
            return []
    
    return selected_playlists

def run_export(manager: SpotifyManager, data_file: str, selective: bool = False):
    """Handles the export process."""
    start_time = time.time()
    logger.info("Starting Spotify data export...")

    playlists_raw = manager.get_all_playlists()
    if playlists_raw is None:  # Check if fetching failed
        logger.error("Failed to fetch playlists. Aborting export.")
        return False

    # Allow user to select specific playlists if in selective mode
    if selective:
        logger.info("Entering selective playlist mode for export.")
        # We need to fetch tracks for selection display
        for p in playlists_raw:
            logger.info(f"Fetching tracks for playlist: {p.get('name', 'Unnamed Playlist')} (ID: {p['id']})")
            tracks = manager.get_playlist_tracks(p['id'])
            p['tracks'] = tracks if tracks is not None else []
        
        playlists_raw = select_playlists(playlists_raw)
        if not playlists_raw:
            logger.info("No playlists selected for export. Operation cancelled.")
            return False
    
    # Process selected playlists for export
    playlist_data = []
    for p in playlists_raw:
        logger.info(f"Processing playlist: {p.get('name', 'Unnamed Playlist')} (ID: {p['id']})")
        
        # If tracks weren't already fetched during selection
        if 'tracks' not in p or selective is False:
            logger.info(f"Fetching tracks for playlist: {p.get('name', 'Unnamed Playlist')}")
            tracks = manager.get_playlist_tracks(p['id'])
            if tracks is None:
                logger.warning(f"Failed to fetch tracks for playlist {p.get('name', 'Unnamed Playlist')}. Skipping tracks.")
                tracks = []
        else:
            tracks = p['tracks']

        playlist_data.append({
            'id': p['id'],
            'name': p.get('name', 'Unnamed Playlist'),
            'public': p.get('public', False),
            'description': p.get('description', ''),
            'tracks': tracks
        })

    # Handle liked songs
    liked_songs = []
    export_liked = True
    
    if selective:
        export_liked = input("\nExport liked songs? (y/n): ").lower().strip() == 'y'
    
    if export_liked:
        logger.info("Fetching liked songs...")
        liked_songs = manager.get_liked_songs()
        if liked_songs is None:
            logger.error("Failed to fetch liked songs. Continuing with playlists only.")
            liked_songs = []
    else:
        logger.info("Skipping liked songs export as per user selection.")

    # Prepare export content
    export_content = {'playlists': playlist_data, 'liked_songs': liked_songs}
    
    try:
        save_data(export_content, data_file)
        logger.info(f"Export completed successfully in {time.time() - start_time:.2f} seconds.")
        logger.info(f"Exported {len(playlist_data)} playlists and {len(liked_songs)} liked songs.")
        return True
    except Exception:
        logger.error("Failed to save exported data to file.")
        return False

def run_import(manager: SpotifyManager, data_file: str, selective: bool = False):
    """Handles the import process."""
    start_time = time.time()
    logger.info("Starting Spotify data import...")

    data_to_import = load_data(data_file)
    if not data_to_import:
        logger.error(f"Could not load data from {data_file}. Aborting import.")
        return False

    # Handle liked songs import
    import_liked = True
    if 'liked_songs' in data_to_import and data_to_import['liked_songs']:
        if selective:
            liked_count = len(data_to_import['liked_songs'])
            import_liked = input(f"\nImport {liked_count} liked songs? (y/n): ").lower().strip() == 'y'
        
        if import_liked:
            manager.add_tracks_to_library(data_to_import['liked_songs'])
        else:
            logger.info("Skipping liked songs import as per user selection.")
    else:
        logger.warning("No liked songs found in data file or empty list.")

    # Handle playlists import
    if 'playlists' in data_to_import and data_to_import['playlists']:
        playlists_to_import = data_to_import['playlists']
        
        # Allow user to select specific playlists if in selective mode
        if selective:
            logger.info("Entering selective playlist mode for import.")
            playlists_to_import = select_playlists(playlists_to_import)
            if not playlists_to_import:
                logger.info("No playlists selected for import.")
                if import_liked:
                    return True  # We imported liked songs, so still consider it a success
                return False
        
        # Import selected playlists
        logger.info(f"Importing {len(playlists_to_import)} playlists...")
        for i, playlist in enumerate(playlists_to_import, 1):
            logger.info(f"--- Processing playlist {i}/{len(playlists_to_import)} ---")
            playlist_name = playlist.get('name', f'Imported Playlist {i}')
            is_public = playlist.get('public', False)
            track_uris = playlist.get('tracks', [])

            if not isinstance(track_uris, list):
                logger.warning(f"Skipping playlist '{playlist_name}' due to invalid 'tracks' format.")
                continue

            manager.create_playlist_and_add_tracks(playlist_name, is_public, track_uris)
            time.sleep(0.5)  # Small delay to avoid rate limits
    else:
        logger.warning("No playlists found in data file or empty list.")

    logger.info(f"Import completed in {time.time() - start_time:.2f} seconds.")
    return True

def run_erase(manager: SpotifyManager, selective: bool = False):
    """Handles the erase process."""
    start_time = time.time()
    logger.warning("Starting Spotify data erasure process.")
    
    if not selective:
        # Confirm full erase with double confirmation for safety
        confirm = input("Are you sure you want to delete ALL playlists and liked songs? This cannot be undone. (yes/no): ").lower()
        if confirm != 'yes':
            logger.info("Erasure cancelled by user.")
            return False
        
        double_confirm = input("Type 'CONFIRM' to proceed with complete erasure: ").strip()
        if double_confirm != 'CONFIRM':
            logger.info("Erasure cancelled by user at second confirmation.")
            return False
    
    # Fetch playlists
    playlists = manager.get_all_playlists()
    if playlists is None:
        logger.error("Failed to fetch playlists. Cannot proceed with playlist deletion.")
        return False
    
    playlists_to_delete = []
    if playlists:
        if selective:
            logger.info("Entering selective playlist mode for deletion.")
            playlists_to_delete = select_playlists(playlists)
            if not playlists_to_delete:
                logger.info("No playlists selected for deletion.")
            else:
                # Additional confirmation for selective deletion
                print("\nYou are about to delete the following playlists:")
                for p in playlists_to_delete:
                    print(f"- {p.get('name', 'Unnamed Playlist')}")
                
                confirm = input("\nProceed with deletion? (yes/no): ").lower()
                if confirm != 'yes':
                    logger.info("Playlist deletion cancelled by user.")
                    playlists_to_delete = []
        else:
            playlists_to_delete = playlists
    
    # Delete selected playlists
    if playlists_to_delete:
        logger.info(f"Deleting {len(playlists_to_delete)} playlists...")
        for i, playlist in enumerate(playlists_to_delete, 1):
            playlist_name = playlist.get('name', 'Unnamed Playlist')
            playlist_id = playlist['id']
            logger.warning(f"Deleting playlist {i}/{len(playlists_to_delete)}: '{playlist_name}'")
            manager.unfollow_playlist(playlist_id)
            time.sleep(0.2)  # Small delay
        logger.info("Finished deleting playlists.")
    else:
        logger.info("No playlists were deleted.")
    
    # Handle liked songs deletion
    delete_liked = False
    if not selective:
        delete_liked = True
    else:
        delete_liked = input("\nDelete liked songs? (yes/no): ").lower() == 'yes'
    
    if delete_liked:
        logger.info("Fetching liked songs to delete...")
        liked_songs = manager.get_liked_songs()
        if liked_songs is None:
            logger.error("Failed to fetch liked songs. Cannot proceed with deletion.")
        elif liked_songs:
            # Final confirmation for liked songs
            confirm = input(f"Delete {len(liked_songs)} liked songs? This cannot be undone. (yes/no): ").lower()
            if confirm == 'yes':
                manager.remove_tracks_from_library(liked_songs)
                logger.info("Finished deleting liked songs.")
            else:
                logger.info("Liked songs deletion cancelled by user.")
        else:
            logger.info("No liked songs found to delete.")
    else:
        logger.info("Skipping liked songs deletion as per user selection.")
    
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
    action_group.add_argument('--gui', action='store_true', help='Launch the graphical user interface.')

    # Options
    parser.add_argument('--selective', '-s', action='store_true', help='Enable interactive selection of playlists.')
    parser.add_argument('--debug', action='store_true', help='Enable detailed debug logging.')
    parser.add_argument('--clean-cache', action='store_true', help='Delete OAuth cache file before authenticating.')
    parser.add_argument('--data-file', type=str, default=config.DATA_FILE, help=f'Specify the JSON file for export/import (default: {config.DATA_FILE})')

    args = parser.parse_args()

    # --- Setup Logging ---
    setup_logging(debug=args.debug)
    logger.info("Logging configured.")
    
    # --- Launch GUI if requested ---
    if args.gui:
        try:
            from .gui import start_gui
            logger.info("Starting GUI mode...")
            start_gui()
            return
        except ImportError as e:
            logger.error(f"Failed to import GUI module: {e}")
            logger.error("Make sure you have tkinter installed (included with most Python installations).")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error starting GUI: {e}", exc_info=True)
            sys.exit(1)
    
    # --- Continue with CLI mode ---
    
    # --- Validate Configuration ---
    if not config.IS_CONFIG_VALID:
        logger.critical("Configuration is invalid. Please check .env file or environment variables. Exiting.")
        sys.exit(1)

    # --- Determine Action and Username ---
    username = None
    action_func = None
    if args.export:
        username = config.EXPORT_USERNAME
        action_func = run_export
        logger.info(f"Action: Export | User: {username} | Selective: {args.selective}")
    elif args.import_data:
        username = config.IMPORT_USERNAME
        action_func = run_import
        logger.info(f"Action: Import | User: {username} | Selective: {args.selective}")
    elif args.erase:
        username = config.ERASE_USERNAME
        action_func = run_erase
        logger.info(f"Action: Erase | User: {username} | Selective: {args.selective}")

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
            success = action_func(manager, args.data_file, args.selective)
        elif action_func == run_import:
            success = action_func(manager, args.data_file, args.selective)
        elif action_func == run_erase:
            success = action_func(manager, args.selective)
    except Exception as e:
        logger.critical(f"An unexpected error occurred during the '{action_func.__name__}' process: {e}", exc_info=True)
        sys.exit(1)

    if success:
        logger.info("Operation finished successfully.")
        sys.exit(0)
    else:
        logger.error("Operation failed. Please review logs.")
        sys.exit(1)

if __name__ == '__main__':
    main()