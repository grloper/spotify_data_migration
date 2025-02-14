import logging
import time
import os
import json
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from logging_config import log
import glob

load_dotenv()

SPOTIFY_SCOPE = 'playlist-modify-public playlist-modify-private user-library-read user-library-modify'

def authenticate(username: str, clean_cache: bool = False) -> spotipy.Spotify:
    """Authenticate a Spotify user."""
    if clean_cache:
        for cache_file in glob.glob(".cache-*"):
            log(f"Deleting cache file: {cache_file}", logging.INFO)
            os.remove(cache_file)
    
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope=SPOTIFY_SCOPE,
        username=username
    ))


def fetch_tracks(sp: spotipy.Spotify, fetch_func, *args) -> list:
    """Generic function to fetch paginated Spotify track data."""
    tracks = []
    try:
        results = fetch_func(*args)
        while results:
            tracks.extend([item['track']['uri'] for item in results['items'] if item['track']])
            results = sp.next(results) if results['next'] else None
    except Exception as e:
        log(f"Error fetching tracks: {e}", logging.ERROR)
    return tracks

def delete_all_playlists_and_likes(debug: bool = False, clean_cache: bool = False):
    """Erase the Spotify account by deleting all playlists and liked songs."""
    start_time = time.time()
    sp = authenticate(os.getenv('EXPORT_USERNAME'), clean_cache)
    
    log("Fetching playlists for deletion...")
    try:
        for playlist in sp.current_user_playlists()['items']:
            log(f"Deleting playlist: {playlist['name']}")
            sp.current_user_unfollow_playlist(playlist['id'])
    except Exception as e:
        log(f"Error deleting playlists: {e}", logging.ERROR)
    
    log("Fetching liked songs for deletion...")
    try:
        liked_songs = fetch_tracks(sp, sp.current_user_saved_tracks)
        for i in range(0, len(liked_songs), 50):
            sp.current_user_saved_tracks_delete(liked_songs[i:i+50])
        log("All liked songs deleted.")
    except Exception as e:
        log(f"Error deleting liked songs: {e}", logging.ERROR)
    
    log(f"delete_all_playlists_and_likes() completed in {time.time() - start_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)

def export_data(debug: bool = False, clean_cache: bool = False):
    """Export user playlists and liked songs to a JSON file."""
    start_time = time.time()
    sp = authenticate(os.getenv('EXPORT_USERNAME'), clean_cache)
    
    log("Fetching playlists...")
    playlist_data = []
    try:
        for playlist in sp.current_user_playlists()['items']:
            log(f"Processing playlist: {playlist['name']}")
            playlist_data.append({
                'id': playlist['id'],
                'name': playlist['name'],
                'public': playlist['public'],
                'tracks': fetch_tracks(sp, sp.playlist_tracks, playlist['id'])
            })
    except Exception as e:
        log(f"Error fetching playlists: {e}", logging.ERROR)
    
    liked_songs = fetch_tracks(sp, sp.current_user_saved_tracks)
    
    try:
        with open('spotify_data.json', 'w') as f:
            json.dump({'playlists': playlist_data, 'liked_songs': liked_songs}, f, indent=4)
        log("Exported data to spotify_data.json")
    except Exception as e:
        log(f"Error writing to file: {e}", logging.ERROR)
    
    log(f"export_data() completed in {time.time() - start_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)

def import_data(debug: bool = False, clean_cache: bool = False):
    """Import playlists and liked songs from a JSON file to Spotify."""
    start_time = time.time()
    sp = authenticate(os.getenv('IMPORT_USERNAME'), clean_cache)
    
    try:
        with open('spotify_data.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        log(f"Error reading data file: {e}", logging.ERROR)
        return
    
    log("Importing liked songs...")
    for i in range(0, len(data['liked_songs']), 50):
        sp.current_user_saved_tracks_add(data['liked_songs'][i:i+50])
    log("Liked songs imported successfully.")
    
    log("Importing playlists...")
    for playlist in data['playlists']:
        log(f"Creating playlist: {playlist['name']}")
        try:
            new_playlist = sp.user_playlist_create(sp.me()['id'], playlist['name'], public=playlist['public'])
            new_playlist_id = new_playlist['id']
            
            for i in range(0, len(playlist['tracks']), 100):
                sp.playlist_add_items(new_playlist_id, playlist['tracks'][i:i+100])
            log(f"Added {len(playlist['tracks'])} tracks to {playlist['name']}")
        except Exception as e:
            log(f"Error creating playlist {playlist['name']}: {e}", logging.ERROR)
    
    log(f"import_data() completed in {time.time() - start_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Manage Spotify data')
    parser.add_argument('--export', action='store_true', help='Export data from Spotify')
    parser.add_argument('--import-data', action='store_true', help='Import data to Spotify')
    parser.add_argument('--erase', action='store_true', help='Delete all playlists and liked songs')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--clean-cache', action='store_true', help='Delete OAuth cache before running')
    
    args = parser.parse_args()
    
    if args.export:
        export_data(debug=args.debug, clean_cache=args.clean_cache)
    elif args.import_data:
        import_data(debug=args.debug, clean_cache=args.clean_cache)
    elif args.erase:
        delete_all_playlists_and_likes(debug=args.debug, clean_cache=args.clean_cache)
