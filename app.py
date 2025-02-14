import logging
import time
import os
import json
import glob
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from logging_config import log

# Load environment variables
load_dotenv()

SPOTIFY_SCOPE = (
    'playlist-modify-public '
    'playlist-modify-private '
    'user-library-read '
    'user-library-modify'
)

CACHE_PATTERN = ".cache-*"
DATA_FILE = "spotify_data.json"


def authenticate(username: str, clean_cache: bool = False) -> spotipy.Spotify:
    """Authenticate a Spotify user."""
    if clean_cache:
        for cache_file in glob.glob(CACHE_PATTERN):
            log(f"Deleting cache file: {cache_file}", logging.INFO)
            os.remove(cache_file)

    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope=SPOTIFY_SCOPE,
        username=username
    ))


def fetch_paginated_data(sp: spotipy.Spotify, fetch_func, *args) -> list:
    """Fetch paginated Spotify data (e.g., tracks, playlists)."""
    items = []
    try:
        results = fetch_func(*args)
        while results:
            items.extend(results['items'])
            results = sp.next(results) if results['next'] else None
    except Exception as e:
        log(f"Error fetching data: {e}", logging.ERROR)
    return items


def erase_all_spotify_data(debug: bool = False, clean_cache: bool = False):
    """Erase all playlists and liked songs from the Spotify account."""
    start_time = time.time()
    sp = authenticate(os.getenv('ERASE_USERNAME'), clean_cache)

    log("Deleting all playlists...")
    playlists = fetch_paginated_data(sp, sp.current_user_playlists)
    for playlist in playlists:
        log(f"Removing playlist: {playlist['name']}")
        sp.current_user_unfollow_playlist(playlist['id'])

    log("Deleting liked songs...")
    liked_songs = [item['track']['uri'] for item in fetch_paginated_data(sp, sp.current_user_saved_tracks) if item.get('track')]
    for i in range(0, len(liked_songs), 50):
        sp.current_user_saved_tracks_delete(liked_songs[i:i + 50])

    log(f"Erasure completed in {time.time() - start_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)


def export_data(debug: bool = False, clean_cache: bool = False):
    """Export user playlists and liked songs to a JSON file."""
    start_time = time.time()
    sp = authenticate(os.getenv('EXPORT_USERNAME'), clean_cache)

    log("Fetching playlists...")
    playlists = fetch_paginated_data(sp, sp.current_user_playlists)
    playlist_data = [{
        'id': p['id'],
        'name': p['name'],
        'public': p['public'],
        'tracks': [t['track']['uri'] for t in fetch_paginated_data(sp, sp.playlist_tracks, p['id']) if t.get('track')]
    } for p in playlists]

    log("Fetching liked songs...")
    liked_songs = [item['track']['uri'] for item in fetch_paginated_data(sp, sp.current_user_saved_tracks) if item.get('track')]

    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({'playlists': playlist_data, 'liked_songs': liked_songs}, f, indent=4)
        log(f"Exported data to {DATA_FILE}")
    except Exception as e:
        log(f"Error writing to file: {e}", logging.ERROR)

    log(f"Export completed in {time.time() - start_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)


def import_data(debug: bool = False, clean_cache: bool = False):
    """Import playlists and liked songs from a JSON file to Spotify."""
    start_time = time.time()
    sp = authenticate(os.getenv('IMPORT_USERNAME'), clean_cache)

    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        log(f"Error reading data file: {e}", logging.ERROR)
        return

    log("Importing liked songs...")
    for i in range(0, len(data['liked_songs']), 50):
        sp.current_user_saved_tracks_add(data['liked_songs'][i:i + 50])

    log("Importing playlists...")
    for playlist in data['playlists']:
        log(f"Creating playlist: {playlist['name']}")
        try:
            new_playlist = sp.user_playlist_create(sp.me()['id'], playlist['name'], public=playlist['public'])
            new_playlist_id = new_playlist['id']

            for i in range(0, len(playlist['tracks']), 100):
                sp.playlist_add_items(new_playlist_id, playlist['tracks'][i:i + 100])

            log(f"Added {len(playlist['tracks'])} tracks to {playlist['name']}")
        except Exception as e:
            log(f"Error creating playlist {playlist['name']}: {e}", logging.ERROR)

    log(f"Import completed in {time.time() - start_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Manage Spotify data")
    parser.add_argument('--export', action='store_true', help='Export data from Spotify')
    parser.add_argument('--import-data', action='store_true', help='Import data to Spotify')
    parser.add_argument('--erase', action='store_true', help='Delete all playlists and liked songs')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--clean-cache', action='store_true', help='Delete OAuth cache before running')

    args = parser.parse_args()

    actions = {
        "export": export_data,
        "import_data": import_data,
        "erase": erase_all_spotify_data
    }

    for action, func in actions.items():
        if getattr(args, action.replace("-", "_"), False):
            func(debug=args.debug, clean_cache=args.clean_cache)
            break
