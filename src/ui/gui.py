import sys
import os
import logging
import json
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QLineEdit, QPushButton, 
                            QFileDialog, QCheckBox, QListWidget, QListWidgetItem,
                            QMessageBox, QProgressBar, QTextEdit, QGroupBox,
                            QFormLayout, QScrollArea, QApplication, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from src.core.spotify_client import SpotifyClient
from src.core.operations import SpotifyOperations
from src.ui.logger import QTextEditLogger

logger = logging.getLogger(__name__)

class Worker(QThread):
    """Worker thread for performing Spotify operations."""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)
    
    def __init__(self, operation, args):
        super().__init__()
        self.operation = operation
        self.args = args
    
    def run(self):
        try:
            result = self.operation(**self.args)
            self.finished.emit(result, "Operation completed successfully" if result else "Operation failed")
        except Exception as e:
            logger.error(f"Error in worker thread: {str(e)}")
            self.finished.emit(False, f"Operation failed: {str(e)}")

class PlaylistSelectionDialog(QDialog):
    """Dialog for selecting playlists."""
    def __init__(self, playlists, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Playlists")
        self.resize(400, 500)
        
        self.playlists = playlists
        self.selected_playlists = []
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create list widget for playlists
        self.list_widget = QListWidget()
        
        # Error handling for playlist data
        if not self.playlists:
            layout.addWidget(QLabel("No playlists found or error loading playlists."))
        else:
            try:
                for playlist in self.playlists:
                    # Validate playlist structure
                    if not isinstance(playlist, dict) or 'name' not in playlist or 'id' not in playlist:
                        logger.error(f"Invalid playlist format: {playlist}")
                        continue
                    
                    # Get track count safely
                    track_count = 0
                    if 'tracks' in playlist and isinstance(playlist['tracks'], dict) and 'total' in playlist['tracks']:
                        track_count = playlist['tracks']['total']
                    
                    item = QListWidgetItem(f"{playlist['name']} ({track_count} tracks)")
                    item.setData(Qt.UserRole, playlist['id'])
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.list_widget.addItem(item)
                
                logger.info(f"Added {self.list_widget.count()} playlists to selection dialog")
            except Exception as e:
                logger.error(f"Error populating playlist list: {str(e)}")
                layout.addWidget(QLabel(f"Error loading playlists: {str(e)}"))
        
        layout.addWidget(QLabel("Select playlists:"))
        layout.addWidget(self.list_widget)
        
        # Buttons for select all/none
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(select_none_btn)
        layout.addLayout(btn_layout)
        
        # OK/Cancel buttons
        ok_cancel_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_cancel_layout.addWidget(ok_btn)
        ok_cancel_layout.addWidget(cancel_btn)
        layout.addLayout(ok_cancel_layout)
        
        self.setLayout(layout)
    
    def select_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked)
    
    def select_none(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def accept(self):
        self.selected_playlists = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_playlists.append(item.data(Qt.UserRole))
        
        logger.info(f"Selected {len(self.selected_playlists)} playlists")
        super().accept()
    
    def reject(self):
        logger.info("Playlist selection canceled")
        super().reject()

class SpotifyMigrationApp(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Data Migration")
        self.resize(800, 600)
        
        self.spotify_client = SpotifyClient()
        self.operations = None
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Setup tab
        setup_tab = QWidget()
        setup_layout = QFormLayout()
        
        self.client_id_input = QLineEdit()
        self.client_secret_input = QLineEdit()
        self.redirect_uri_input = QLineEdit()
        self.redirect_uri_input.setText("http://localhost:8888/callback")
        
        setup_layout.addRow("Client ID:", self.client_id_input)
        setup_layout.addRow("Client Secret:", self.client_secret_input)
        setup_layout.addRow("Redirect URI:", self.redirect_uri_input)
        
        self.auth_button = QPushButton("Authenticate")
        self.auth_button.clicked.connect(self.authenticate)
        setup_layout.addRow("", self.auth_button)
        
        self.auth_status = QLabel("Not authenticated")
        setup_layout.addRow("Status:", self.auth_status)
        
        setup_tab.setLayout(setup_layout)
        
        # Export tab
        export_tab = QWidget()
        export_layout = QVBoxLayout()
        
        export_options_group = QGroupBox("Export Options")
        export_options_layout = QVBoxLayout()
        
        self.export_playlists_cb = QCheckBox("Export Playlists")
        self.export_playlists_cb.setChecked(True)
        self.export_liked_songs_cb = QCheckBox("Export Liked Songs")
        self.export_liked_songs_cb.setChecked(True)
        
        export_options_layout.addWidget(self.export_playlists_cb)
        export_options_layout.addWidget(self.export_liked_songs_cb)
        
        self.select_playlists_btn = QPushButton("Select Playlists")
        self.select_playlists_btn.clicked.connect(self.select_export_playlists)
        export_options_layout.addWidget(self.select_playlists_btn)
        
        export_options_group.setLayout(export_options_layout)
        export_layout.addWidget(export_options_group)
        
        self.export_file_path = QLineEdit()
        self.export_file_path.setReadOnly(True)
        export_file_btn = QPushButton("Select Export File")
        export_file_btn.clicked.connect(self.select_export_file)
        
        export_file_layout = QHBoxLayout()
        export_file_layout.addWidget(QLabel("Export File:"))
        export_file_layout.addWidget(self.export_file_path)
        export_file_layout.addWidget(export_file_btn)
        export_layout.addLayout(export_file_layout)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        export_layout.addWidget(self.export_btn)
        
        export_tab.setLayout(export_layout)
        
        # Import tab
        import_tab = QWidget()
        import_layout = QVBoxLayout()
        
        import_options_group = QGroupBox("Import Options")
        import_options_layout = QVBoxLayout()
        
        self.import_playlists_cb = QCheckBox("Import Playlists")
        self.import_playlists_cb.setChecked(True)
        self.import_liked_songs_cb = QCheckBox("Import Liked Songs")
        self.import_liked_songs_cb.setChecked(True)
        
        import_options_layout.addWidget(self.import_playlists_cb)
        import_options_layout.addWidget(self.import_liked_songs_cb)
        
        self.select_import_playlists_btn = QPushButton("Select Playlists to Import")
        self.select_import_playlists_btn.clicked.connect(self.select_import_playlists)
        import_options_layout.addWidget(self.select_import_playlists_btn)
        
        import_options_group.setLayout(import_options_layout)
        import_layout.addWidget(import_options_group)
        
        self.import_file_path = QLineEdit()
        self.import_file_path.setReadOnly(True)
        import_file_btn = QPushButton("Select Import File")
        import_file_btn.clicked.connect(self.select_import_file)
        
        import_file_layout = QHBoxLayout()
        import_file_layout.addWidget(QLabel("Import File:"))
        import_file_layout.addWidget(self.import_file_path)
        import_file_layout.addWidget(import_file_btn)
        import_layout.addLayout(import_file_layout)
        
        self.import_btn = QPushButton("Import Data")
        self.import_btn.clicked.connect(self.import_data)
        import_layout.addWidget(self.import_btn)
        
        import_tab.setLayout(import_layout)
        
        # Erase tab
        erase_tab = QWidget()
        erase_layout = QVBoxLayout()
        
        erase_options_group = QGroupBox("Erase Options")
        erase_options_layout = QVBoxLayout()
        
        self.erase_playlists_cb = QCheckBox("Erase Playlists")
        self.erase_playlists_cb.setChecked(True)
        self.erase_liked_songs_cb = QCheckBox("Erase Liked Songs")
        self.erase_liked_songs_cb.setChecked(True)
        
        erase_options_layout.addWidget(self.erase_playlists_cb)
        erase_options_layout.addWidget(self.erase_liked_songs_cb)
        
        self.select_erase_playlists_btn = QPushButton("Select Playlists to Erase")
        self.select_erase_playlists_btn.clicked.connect(self.select_erase_playlists)
        erase_options_layout.addWidget(self.select_erase_playlists_btn)
        
        erase_options_group.setLayout(erase_options_layout)
        erase_layout.addWidget(erase_options_group)
        
        self.erase_btn = QPushButton("Erase Data")
        self.erase_btn.clicked.connect(self.erase_data)
        erase_layout.addWidget(self.erase_btn)
        
        # Add warning message
        warning_label = QLabel("Warning: Erasing data will permanently remove the selected content from your Spotify account.")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        erase_layout.addWidget(warning_label)
        
        erase_tab.setLayout(erase_layout)
        
        # Add tabs to tab widget
        self.tabs.addTab(setup_tab, "Setup")
        self.tabs.addTab(export_tab, "Export")
        self.tabs.addTab(import_tab, "Import")
        self.tabs.addTab(erase_tab, "Erase")
        
        # Log viewer
        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        log_handler = QTextEditLogger(self.log_text)
        log_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(log_handler)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add all widgets to main layout
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(log_group)
        main_layout.addWidget(self.progress_bar)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Disable operation tabs until authenticated
        self.update_tab_states(False)
        
        # Set up instance variables
        self.export_selected_playlists = []
        self.import_selected_playlists = []
        self.erase_selected_playlists = []
        self.playlists_data = []
    
    def update_tab_states(self, authenticated):
        """Enable or disable operation tabs based on authentication status."""
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, authenticated)
    
    def authenticate(self):
        """Authenticate with Spotify."""
        try:
            # Disable the auth button while authenticating
            self.auth_button.setEnabled(False)
            self.auth_status.setText("Authenticating...")
            QApplication.processEvents()  # Ensure UI updates
            
            client_id = self.client_id_input.text().strip()
            client_secret = self.client_secret_input.text().strip()
            redirect_uri = self.redirect_uri_input.text().strip()
            
            if not client_id or not client_secret or not redirect_uri:
                QMessageBox.warning(self, "Authentication Error", "Please provide valid credentials.")
                self.auth_status.setText("Authentication failed: Missing credentials")
                return
            
            # Create a new Spotify client
            try:
                self.spotify_client = SpotifyClient(client_id, client_secret, redirect_uri)
                logger.info("Created SpotifyClient instance")
            except Exception as e:
                logger.error(f"Error creating SpotifyClient: {str(e)}")
                self.auth_status.setText("Error creating Spotify client")
                QMessageBox.critical(self, "Error", f"Failed to create Spotify client: {str(e)}")
                return
            
            # Try to authenticate
            authenticated = False
            try:
                logger.info("Attempting authentication...")
                authenticated = self.spotify_client.authenticate()
                logger.info(f"Authentication result: {authenticated}")
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Authentication error: {str(e)}\n{tb}")
                
                # Check for specific errors
                error_msg = str(e).lower()
                if "redirect_uri_mismatch" in error_msg:
                    msg = ("Redirect URI mismatch. Please verify that the redirect URI exactly matches "
                           "what you've registered in your Spotify Developer Dashboard.")
                elif "invalid_client" in error_msg:
                    msg = "Invalid Client ID or Client Secret. Please check your credentials."
                else:
                    msg = f"Authentication failed: {str(e)}"
                
                self.auth_status.setText("Authentication failed")
                QMessageBox.critical(self, "Authentication Error", msg)
                return
            
            # Check authentication result
            if authenticated and self.spotify_client.user_id:
                self.auth_status.setText(f"Authenticated as {self.spotify_client.user_id}")
                self.operations = SpotifyOperations(self.spotify_client)
                self.update_tab_states(True)
                
                # Load playlists
                try:
                    logger.info("Loading playlists...")
                    self.playlists_data = self.spotify_client.get_playlists()
                    logger.info(f"Loaded {len(self.playlists_data)} playlists")
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(f"Error loading playlists: {str(e)}\n{tb}")
                    QMessageBox.warning(self, "Playlist Loading Error", 
                                        f"Authentication successful, but there was an error loading playlists: {str(e)}")
                    self.playlists_data = []
            else:
                self.auth_status.setText("Authentication failed")
                QMessageBox.critical(self, "Authentication Error", 
                                    "Failed to authenticate with Spotify. Check your credentials and try again.")
                self.update_tab_states(False)
        
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Unexpected error during authentication: {str(e)}\n{tb}")
            self.auth_status.setText("Authentication error")
            QMessageBox.critical(self, "Unexpected Error", 
                                f"An unexpected error occurred during authentication:\n{str(e)}")
            self.update_tab_states(False)
        
        finally:
            # Always re-enable the auth button
            self.auth_button.setEnabled(True)
    
    def select_export_playlists(self):
        """Open dialog to select playlists for export."""
        try:
            if not self.spotify_client or not self.spotify_client.sp:
                QMessageBox.warning(self, "Not Authenticated", "Please authenticate with Spotify first.")
                return
            
            if not self.playlists_data:
                try:
                    logger.info("Attempting to refresh playlists data")
                    self.playlists_data = self.spotify_client.get_playlists()
                    if not self.playlists_data:
                        QMessageBox.warning(self, "No Playlists", "No playlists found in your account.")
                        return
                except Exception as e:
                    logger.error(f"Error refreshing playlists: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Could not load playlists: {str(e)}")
                    return
            
            dialog = PlaylistSelectionDialog(self.playlists_data, self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.export_selected_playlists = dialog.selected_playlists
                logger.info(f"Selected {len(self.export_selected_playlists)} playlists for export")
                
                # Update UI to show selection
                if self.export_selected_playlists:
                    self.select_playlists_btn.setText(f"Select Playlists ({len(self.export_selected_playlists)} selected)")
                else:
                    self.select_playlists_btn.setText("Select Playlists")
        
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error in playlist selection: {str(e)}\n{tb}")
            QMessageBox.critical(self, "Error", f"An error occurred while selecting playlists: {str(e)}")
    
    def select_import_playlists(self):
        """Open dialog to select playlists for import."""
        try:
            if not self.import_file_path.text():
                QMessageBox.warning(self, "No Import File", "Please select an import file first.")
                return
            
            try:
                with open(self.import_file_path.text(), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'playlists' not in data or not data['playlists']:
                    QMessageBox.warning(self, "No Playlists", "No playlists found in the import file.")
                    return
                
                playlists = []
                for playlist in data.get('playlists', []):
                    try:
                        playlists.append({
                            'id': playlist['id'],
                            'name': playlist['name'],
                            'tracks': {'total': len(playlist.get('tracks', []))}
                        })
                    except KeyError as ke:
                        logger.error(f"Missing key in playlist data: {ke}")
                
                if not playlists:
                    QMessageBox.warning(self, "Invalid Data", "Could not find valid playlist data in the import file.")
                    return
                
                dialog = PlaylistSelectionDialog(playlists, self)
                result = dialog.exec_()
                
                if result == QDialog.Accepted:
                    self.import_selected_playlists = dialog.selected_playlists
                    logger.info(f"Selected {len(self.import_selected_playlists)} playlists for import")
                    
                    # Update UI to show selection
                    if self.import_selected_playlists:
                        self.select_import_playlists_btn.setText(f"Select Playlists ({len(self.import_selected_playlists)} selected)")
                    else:
                        self.select_import_playlists_btn.setText("Select Playlists to Import")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                QMessageBox.critical(self, "Error", f"The import file contains invalid JSON: {str(e)}")
            except Exception as e:
                logger.error(f"Error reading import file: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to read import file: {str(e)}")
        
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Unexpected error in import playlist selection: {str(e)}\n{tb}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def select_erase_playlists(self):
        """Open dialog to select playlists for erasure."""
        try:
            if not self.spotify_client or not self.spotify_client.sp:
                QMessageBox.warning(self, "Not Authenticated", "Please authenticate with Spotify first.")
                return
            
            if not self.playlists_data:
                try:
                    logger.info("Attempting to refresh playlists data for erase")
                    self.playlists_data = self.spotify_client.get_playlists()
                    if not self.playlists_data:
                        QMessageBox.warning(self, "No Playlists", "No playlists found in your account.")
                        return
                except Exception as e:
                    logger.error(f"Error refreshing playlists: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Could not load playlists: {str(e)}")
                    return
            
            dialog = PlaylistSelectionDialog(self.playlists_data, self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.erase_selected_playlists = dialog.selected_playlists
                logger.info(f"Selected {len(self.erase_selected_playlists)} playlists for erasure")
                
                # Update UI to show selection
                if self.erase_selected_playlists:
                    self.select_erase_playlists_btn.setText(f"Select Playlists ({len(self.erase_selected_playlists)} selected)")
                else:
                    self.select_erase_playlists_btn.setText("Select Playlists to Erase")
        
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error in erase playlist selection: {str(e)}\n{tb}")
            QMessageBox.critical(self, "Error", f"An error occurred while selecting playlists: {str(e)}")
    
    def select_export_file(self):
        """Select file for exporting data."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Export File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            self.export_file_path.setText(file_path)
    
    def select_import_file(self):
        """Select file for importing data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Import File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.import_file_path.setText(file_path)
    
    def export_data(self):
        """Export data from Spotify."""
        if not self.spotify_client.sp:
            QMessageBox.warning(self, "Not Authenticated", "Please authenticate with Spotify first.")
            return
        
        if self.export_file_path.text() == "":
            QMessageBox.warning(self, "No Export File", "Please select an export file path.")
            return
        
        export_playlists = self.export_playlists_cb.isChecked()
        export_liked_songs = self.export_liked_songs_cb.isChecked()
        
        if not export_playlists and not export_liked_songs:
            QMessageBox.warning(self, "No Selection", "Please select at least one type of data to export.")
            return
        
        args = {
            "export_playlists": export_playlists,
            "export_liked_songs": export_liked_songs,
            "selected_playlists": self.export_selected_playlists if self.export_selected_playlists else None,
            "output_path": self.export_file_path.text()
        }
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.worker = Worker(self.operations.export_data, args)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()
    
    def import_data(self):
        """Import data to Spotify."""
        if not self.spotify_client.sp:
            QMessageBox.warning(self, "Not Authenticated", "Please authenticate with Spotify first.")
            return
        
        if not self.import_file_path.text():
            QMessageBox.warning(self, "No Import File", "Please select an import file.")
            return
        
        import_playlists = self.import_playlists_cb.isChecked()
        import_liked_songs = self.import_liked_songs_cb.isChecked()
        
        if not import_playlists and not import_liked_songs:
            QMessageBox.warning(self, "No Selection", "Please select at least one type of data to import.")
            return
        
        args = {
            "import_file": self.import_file_path.text(),
            "import_playlists": import_playlists,
            "import_liked_songs": import_liked_songs,
            "selected_playlists": self.import_selected_playlists if self.import_selected_playlists else None
        }
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.worker = Worker(self.operations.import_data, args)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()
    
    def erase_data(self):
        """Erase data from Spotify."""
        if not self.spotify_client.sp:
            QMessageBox.warning(self, "Not Authenticated", "Please authenticate with Spotify first.")
            return
        
        erase_playlists = self.erase_playlists_cb.isChecked()
        erase_liked_songs = self.erase_liked_songs_cb.isChecked()
        
        if not erase_playlists and not erase_liked_songs:
            QMessageBox.warning(self, "No Selection", "Please select at least one type of data to erase.")
            return
        
        # Confirm erasure
        message = "Are you sure you want to erase the selected data? This action cannot be undone."
        if QMessageBox.question(self, "Confirm Erasure", message, 
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return
        
        args = {
            "erase_playlists": erase_playlists,
            "erase_liked_songs": erase_liked_songs,
            "selected_playlists": self.erase_selected_playlists if self.erase_selected_playlists else None
        }
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.worker = Worker(self.operations.erase_data, args)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()
    
    def on_operation_finished(self, success, message):
        """Handle operation completion."""
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Operation Complete", message)
        else:
            QMessageBox.critical(self, "Operation Failed", message)