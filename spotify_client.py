import os
import logging
import json
import traceback
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None
        self.user_id = None
        
    def authenticate(self, scope="playlist-read-private playlist-modify-private playlist-modify-public user-library-read user-library-modify"):
        """Authenticate with Spotify."""
        if not self.client_id or not self.client_secret or not self.redirect_uri:
            logger.error("Missing Spotify API credentials")
            return False
        
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
                    raise SpotifyException(
                        status=spotify_err.http_status,
                        code=spotify_err.code,
                        msg="Redirect URI mismatch. Make sure the URI matches exactly with what's registered in Spotify Developer Dashboard."
                    )
                else:
                    logger.error(f"Spotify API error: {str(spotify_err)}")
                    self.sp = None  # Clear the invalid client
                    raise
            
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Authentication error: {str(e)}\n{tb}")
            
            # Clean up resources
            self.sp = None
            self.user_id = None
            
            # Re-raise the exception so the GUI can handle it appropriately
            raise
    
    def get_playlists(self):
        """Get all playlists for the authenticated user."""
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
    
    def get_playlist_tracks(self, playlist_id):
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
    
    def get_liked_songs(self):
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
    
    def create_playlist(self, name, public=False, description=""):
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
    
    def add_tracks_to_playlist(self, playlist_id, track_uris):
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
    
    def like_songs(self, track_ids):
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
    
    def delete_playlist(self, playlist_id):
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
    
    def unlike_songs(self, track_ids):
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
