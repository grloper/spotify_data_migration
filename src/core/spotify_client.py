import os
import logging
import json
import traceback
import time
from functools import wraps
from typing import Dict, List, Optional, Any, Union, Tuple

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

logger = logging.getLogger(__name__)

def retry_on_rate_limit(max_retries=3, initial_backoff=1):
    """Decorator to retry API calls when rate limit is hit."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            backoff = initial_backoff
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except SpotifyException as e:
                    if "rate limit" in str(e).lower() and retries < max_retries:
                        retries += 1
                        sleep_time = backoff * (2 ** (retries - 1))  # Exponential backoff
                        logger.warning(f"Rate limit hit. Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                    else:
                        raise
        return wrapper
    return decorator

class SpotifyAuthError(Exception):
    """Exception raised for authentication errors with Spotify."""
    pass

class SpotifyDataError(Exception):
    """Exception raised for data processing errors."""
    pass

class SpotifyClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, 
                 redirect_uri: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None
        self.user_id = None
        
    def authenticate(self, scope: str = "playlist-read-private playlist-modify-private playlist-modify-public user-library-read user-library-modify") -> bool:
        """
        Authenticate with Spotify.
        
        Args:
            scope: Spotify API permission scopes
            
        Returns:
            bool: True if authentication successful
        """
        if not self.client_id or not self.client_secret or not self.redirect_uri:
            logger.error("Missing Spotify API credentials")
            raise SpotifyAuthError("Missing Spotify API credentials")
        
        try:
            logger.info(f"Authenticating with redirect URI: {self.redirect_uri}")
            
            # Create the auth manager with cache disabled to prevent file permission issues
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                open_browser=True,
                cache_path=None  # Disable caching to avoid file permission issues
            )
            
            # Create the Spotify instance
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection by getting the current user
            try:
                user_info = self.sp.current_user()
                if not user_info or 'id' not in user_info:
                    logger.error("Invalid user info received")
                    return False
                
                self.user_id = user_info['id']
                logger.info(f"Successfully authenticated as user: {self.user_id}")
                return True
            except SpotifyException as spotify_err:
                error_msg = str(spotify_err).lower()
                if "redirect_uri_mismatch" in error_msg:
                    logger.error(f"Redirect URI mismatch. Configured: {self.redirect_uri}")
                    self.sp = None  # Clear the invalid client
                    raise SpotifyAuthError("Redirect URI mismatch. Make sure the URI matches exactly with what's registered in Spotify Developer Dashboard.")
                else:
                    logger.error(f"Spotify API error: {str(spotify_err)}")
                    self.sp = None  # Clear the invalid client
                    raise SpotifyAuthError(f"Spotify API error: {str(spotify_err)}")
            
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Authentication error: {str(e)}\n{tb}")
            
            # Clean up resources
            self.sp = None
            self.user_id = None
            
            # Re-raise the exception so the GUI can handle it appropriately
            raise
    
    @retry_on_rate_limit()
    def get_playlists(self, playlist_ids=None) -> List[Dict[str, Any]]:
        """Get all playlists for the authenticated user or specific playlists by ID."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return []
            
        try:
            playlists = []
            results = self.sp.current_user_playlists(limit=50)  # Use a larger limit to reduce API calls
            
            # Log the first result to help with debugging
            logger.debug(f"First playlist response: {json.dumps(results)[:200]}...")
            
            while results:
                playlists.extend(results['items'])
                logger.info(f"Retrieved {len(results['items'])} playlists, total so far: {len(playlists)}")
                
                if results['next']:
                    try:
                        results = self.sp.next(results)
                    except Exception as e:
                        logger.error(f"Error getting next page of playlists: {str(e)}")
                        break
                else:
                    results = None
            
            # Filter by playlist_ids if provided
            if playlist_ids:
                playlists = [p for p in playlists if p['id'] in playlist_ids]
            
            # Validate each playlist to ensure it has required fields
            valid_playlists = []
            for playlist in playlists:
                if not isinstance(playlist, dict):
                    logger.warning(f"Skipping invalid playlist format: {type(playlist)}")
                    continue
                    
                if 'id' not in playlist or 'name' not in playlist:
                    logger.warning(f"Skipping playlist missing required fields: {playlist.keys()}")
                    continue
                    
                valid_playlists.append(playlist)
            
            logger.info(f"Retrieved {len(valid_playlists)} valid playlists")
            return valid_playlists
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error getting playlists: {str(e)}\n{tb}")
            return []
    
    @retry_on_rate_limit()
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks from a playlist."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return []
            
        try:
            tracks = []
            results = self.sp.playlist_items(playlist_id)
            while results:
                for item in results['items']:
                    if item['track']:
                        tracks.append(item['track'])
                if results['next']:
                    results = self.sp.next(results)
                else:
                    results = None
            logger.info(f"Retrieved {len(tracks)} tracks from playlist")
            return tracks
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {str(e)}")
            return []
    
    @retry_on_rate_limit()
    def get_liked_songs(self) -> List[Dict[str, Any]]:
        """Get user's liked songs."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return []
            
        try:
            tracks = []
            results = self.sp.current_user_saved_tracks()
            while results:
                for item in results['items']:
                    tracks.append(item['track'])
                if results['next']:
                    results = self.sp.next(results)
                else:
                    results = None
            logger.info(f"Retrieved {len(tracks)} liked songs")
            return tracks
        except Exception as e:
            logger.error(f"Error getting liked songs: {str(e)}")
            return []
    
    @retry_on_rate_limit()
    def create_playlist(self, name: str, public: bool = False, description: str = "") -> Optional[Dict[str, Any]]:
        """Create a new playlist."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return None
            
        try:
            playlist = self.sp.user_playlist_create(
                self.user_id, 
                name, 
                public=public, 
                description=description
            )
            logger.info(f"Created playlist: {name}")
            return playlist
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            return None
    
    @retry_on_rate_limit()
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> bool:
        """Add tracks to a playlist."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            # Spotify API allows a maximum of 100 tracks per request
            for i in range(0, len(track_uris), 100):
                chunk = track_uris[i:i+100]
                self.sp.playlist_add_items(playlist_id, chunk)
            logger.info(f"Added {len(track_uris)} tracks to playlist")
            return True
        except Exception as e:
            logger.error(f"Error adding tracks to playlist: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def add_playlists(self, data: Dict[str, Any], playlist_ids: Optional[List[str]] = None) -> bool:
        """Add playlists from exported data."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            if 'playlists' not in data:
                logger.error("No playlists found in import data")
                return False
                
            for playlist_data in data['playlists']:
                # Skip if not in selected playlists
                if playlist_ids and playlist_data['id'] not in playlist_ids:
                    continue
                
                # Create new playlist
                new_playlist = self.create_playlist(
                    name=playlist_data['name'],
                    public=playlist_data.get('public', False),
                    description=playlist_data.get('description', '')
                )
                
                if new_playlist:
                    # Add tracks to playlist
                    track_uris = [track['uri'] for track in playlist_data['tracks'] if 'uri' in track]
                    if track_uris:
                        self.add_tracks_to_playlist(new_playlist['id'], track_uris)
                        logger.info(f"Added {len(track_uris)} tracks to playlist {playlist_data['name']}")
            
            return True
        except Exception as e:
            logger.error(f"Error importing playlists: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def add_liked_songs(self, data: Dict[str, Any]) -> bool:
        """Add liked songs from exported data."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            if 'liked_songs' not in data:
                logger.error("No liked songs found in import data")
                return False
                
            track_ids = [track['id'] for track in data['liked_songs'] if 'id' in track]
            if track_ids:
                self.like_songs(track_ids)
                logger.info(f"Imported {len(track_ids)} liked songs")
            
            return True
        except Exception as e:
            logger.error(f"Error importing liked songs: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def like_songs(self, track_ids: List[str]) -> bool:
        """Like (save) tracks for the user."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            # Spotify API allows a maximum of 50 tracks per request
            for i in range(0, len(track_ids), 50):
                chunk = track_ids[i:i+50]
                self.sp.current_user_saved_tracks_add(tracks=chunk)
            logger.info(f"Liked {len(track_ids)} songs")
            return True
        except Exception as e:
            logger.error(f"Error liking songs: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def delete_playlists(self, playlist_ids: List[str]) -> bool:
        """Delete multiple playlists."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            deleted_count = 0
            for playlist_id in playlist_ids:
                if self.delete_playlist(playlist_id):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} playlists")
            return True
        except Exception as e:
            logger.error(f"Error deleting playlists: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete (unfollow) a playlist."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            self.sp.current_user_unfollow_playlist(playlist_id)
            logger.info(f"Deleted playlist with ID: {playlist_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting playlist: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def delete_liked_songs(self) -> bool:
        """Delete all liked songs."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            liked_songs = self.get_liked_songs()
            track_ids = [track['id'] for track in liked_songs if 'id' in track]
            
            if track_ids:
                self.unlike_songs(track_ids)
                logger.info(f"Deleted {len(track_ids)} liked songs")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting liked songs: {str(e)}")
            return False
    
    @retry_on_rate_limit()
    def unlike_songs(self, track_ids: List[str]) -> bool:
        """Unlike (remove) saved tracks for the user."""
        if not self.sp:
            logger.error("Not authenticated with Spotify")
            return False
            
        try:
            # Spotify API allows a maximum of 50 tracks per request
            for i in range(0, len(track_ids), 50):
                chunk = track_ids[i:i+50]
                self.sp.current_user_saved_tracks_delete(tracks=chunk)
            logger.info(f"Unliked {len(track_ids)} songs")
            return True
        except Exception as e:
            logger.error(f"Error unliking songs: {str(e)}")
            return False