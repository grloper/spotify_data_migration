import os
import json
import base64
import logging
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class CredentialManager:
    """Securely manage API credentials."""
    
    def __init__(self, app_name: str = "SpotifyMigrationTool"):
        self.app_name = app_name
        self.credentials_file = os.path.expanduser(f"~/.{app_name.lower()}_credentials")
        self._key = None
    
    def _generate_key(self, password: str) -> bytes:
        """Generate encryption key from password."""
        salt = b'spotify_migration_salt'  # In production, use a proper random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def set_master_password(self, password: str) -> None:
        """Set the master password for encryption/decryption."""
        self._key = self._generate_key(password)
    
    def save_credentials(self, 
                        client_id: str, 
                        client_secret: str, 
                        redirect_uri: str) -> bool:
        """Encrypt and save credentials to file."""
        if not self._key:
            logger.error("Master password not set")
            return False
            
        try:
            cipher = Fernet(self._key)
            credentials = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }
            
            encrypted_data = cipher.encrypt(json.dumps(credentials).encode())
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info("Credentials saved securely")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {str(e)}")
            return False
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Load and decrypt credentials from file."""
        if not self._key:
            logger.error("Master password not set")
            return None
            
        if not os.path.exists(self.credentials_file):
            logger.warning("No saved credentials found")
            return None
            
        try:
            cipher = Fernet(self._key)
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            logger.info("Credentials loaded successfully")
            return credentials
        except Exception as e:
            logger.error(f"Failed to load credentials: {str(e)}")
            return None
