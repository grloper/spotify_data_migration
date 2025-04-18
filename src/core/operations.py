import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import contextmanager

from src.core.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)

class SpotifyOperations:
    """Controller class handling business logic for Spotify operations."""
    
    def __init__(self, client: SpotifyClient):
        self.client = client

    @contextmanager
    def operation_context(self, operation_name: str):
        """Context manager for operations to standardize error handling."""
        start_time = datetime.now()
        logger.info(f"Starting {operation_name}")
        try:
            yield
            elapsed = datetime.now() - start_time
            logger.info(f"Completed {operation_name} in {elapsed.total_seconds():.2f} seconds")
        except Exception as e:
            logger.error(f"Error during {operation_name}: {str(e)}")
            raise

    def export_data(self, export_playlists=True, export_liked_songs=True, 
                    selected_playlists=None, output_path=None):
        """
        Export data from Spotify to a JSON file.
        
        Args:
            export_playlists: Whether to export playlists
            export_liked_songs: Whether to export liked songs
            selected_playlists: List of specific playlist IDs to export
            output_path: Path to save the export file
            
        Returns:
            bool: Success or failure
        """
        with self.operation_context("data export"):
            try:
                data = {
                    "user_id": self.client.user_id,
                    "export_date": datetime.now().isoformat(),
                    "playlists": [],
                    "liked_songs": []
                }
                
                if export_playlists:
                    playlists = self.client.get_playlists()
                    if selected_playlists:
                        playlists = [p for p in playlists if p['id'] in selected_playlists]
                    
                    for playlist in playlists:
                        playlist_data = {
                            "id": playlist['id'],
                            "name": playlist['name'],
                            "description": playlist.get('description', ''),
                            "public": playlist.get('public', False),
                            "tracks": []
                        }
                        
                        # Get tracks for each playlist
                        tracks = self.client.get_playlist_tracks(playlist['id'])
                        playlist_data["tracks"] = tracks
                        
                        data["playlists"].append(playlist_data)
                
                if export_liked_songs:
                    data["liked_songs"] = self.client.get_liked_songs()

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                logger.info(f"Data exported successfully to {output_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to export data: {e}")
                return False

    def import_data(self, import_type=None, file_path=None, playlist_ids=None, 
                    import_playlists=False, import_liked_songs=False, import_file=None, 
                    selected_playlists=None):
        """
        Import data from a JSON file to Spotify.
        
        Args:
            import_type: Type of data to import ("playlists", "liked_songs", or "both")
            file_path: Path to the JSON file
            playlist_ids: Optional list of playlist IDs to import
            import_playlists: Whether to import playlists
            import_liked_songs: Whether to import liked songs 
            import_file: Alternative path to the JSON file
            selected_playlists: Optional list of selected playlist IDs
            
        Returns:
            bool: Success or failure
        """
        with self.operation_context("data import"):
            try:
                # Handle different parameter combinations for backward compatibility
                actual_file_path = file_path or import_file
                actual_playlist_ids = playlist_ids or selected_playlists
                
                if not actual_file_path:
                    logger.error("No import file specified")
                    return False
                
                with open(actual_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                success = True
                
                # Handle various ways the import type could be specified
                import_playlists_flag = import_playlists or import_type in ["playlists", "both"] 
                import_liked_songs_flag = import_liked_songs or import_type in ["liked_songs", "both"]
                
                if import_playlists_flag:
                    if 'playlists' in data:
                        playlists_success = self.client.add_playlists(data, actual_playlist_ids)
                        if not playlists_success:
                            success = False
                            logger.warning("Failed to import some or all playlists")
                    else:
                        logger.warning("No playlists found in import file")
                
                if import_liked_songs_flag:
                    if 'liked_songs' in data:
                        liked_success = self.client.add_liked_songs(data)
                        if not liked_success:
                            success = False
                            logger.warning("Failed to import liked songs")
                    else:
                        logger.warning("No liked songs found in import file")
                
                return success
                
            except Exception as e:
                logger.error(f"Failed to import data: {e}")
                return False

    def erase_data(self, erase_type=None, playlist_ids=None, 
                   erase_playlists=False, erase_liked_songs=False, 
                   selected_playlists=None):
        """
        Erase data from Spotify.
        
        Args:
            erase_type: Type of data to erase ("playlists", "liked_songs", or "both")
            playlist_ids: Optional list of playlist IDs to erase
            erase_playlists: Whether to erase playlists
            erase_liked_songs: Whether to erase liked songs
            selected_playlists: Optional list of selected playlist IDs
            
        Returns:
            bool: Success or failure
        """
        with self.operation_context("data erase"):
            try:
                success = True
                actual_playlist_ids = playlist_ids or selected_playlists
                
                # Handle various ways the erase type could be specified
                erase_playlists_flag = erase_playlists or erase_type in ["playlists", "both"]
                erase_liked_songs_flag = erase_liked_songs or erase_type in ["liked_songs", "both"]
                
                if erase_playlists_flag:
                    if actual_playlist_ids:
                        playlists_success = self.client.delete_playlists(actual_playlist_ids)
                        if not playlists_success:
                            success = False
                            logger.warning("Failed to delete some or all playlists")
                    else:
                        logger.warning("No playlists selected for deletion")
                
                if erase_liked_songs_flag:
                    liked_success = self.client.delete_liked_songs()
                    if not liked_success:
                        success = False
                        logger.warning("Failed to delete liked songs")
                
                return success
                
            except Exception as e:
                logger.error(f"Failed to erase data: {e}")
                return False
