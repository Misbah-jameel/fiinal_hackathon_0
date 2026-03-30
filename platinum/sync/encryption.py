"""
Vault Encryption

Optional encryption for sensitive vault data.
Uses Fernet symmetric encryption for file-level encryption.
"""

import logging
import base64
import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class VaultEncryption:
    """
    Vault Encryption
    
    Optional encryption for sensitive files:
    - Uses Fernet symmetric encryption
    - Key stored in environment variable or key file
    - Encrypts individual files, not entire vault
    """
    
    def __init__(self, key: Optional[str] = None, key_file: Optional[Path] = None):
        self.key = key or os.getenv("VAULT_ENCRYPTION_KEY")
        self.key_file = key_file
        
        if not self.key and self.key_file and self.key_file.exists():
            self.key = self.key_file.read_text().strip()
        
        self.fernet = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Initialize Fernet encryption"""
        if not self.key:
            logger.warning("No encryption key provided - encryption disabled")
            return
        
        try:
            from cryptography.fernet import Fernet
            
            # Ensure key is valid length
            if isinstance(self.key, str):
                key_bytes = self.key.encode()
            else:
                key_bytes = self.key
            
            # If key is not 32 bytes, derive one
            if len(key_bytes) != 32:
                import hashlib
                key_bytes = hashlib.sha256(self.key.encode()).digest()
            
            # Fernet requires base64-encoded 32-byte key
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            self.fernet = Fernet(fernet_key)
            
            logger.info("Encryption initialized")
            
        except ImportError:
            logger.warning("cryptography not installed - encryption disabled")
        except Exception as e:
            logger.error(f"Encryption initialization failed: {e}")
    
    def encrypt_file(self, filepath: Path) -> Optional[Path]:
        """Encrypt a file"""
        if not self.fernet:
            logger.warning("Encryption not available")
            return None
        
        try:
            content = filepath.read_bytes()
            encrypted = self.fernet.encrypt(content)
            
            # Write encrypted file
            encrypted_path = filepath.with_suffix(filepath.suffix + ".enc")
            encrypted_path.write_bytes(encrypted)
            
            # Remove original
            filepath.unlink()
            
            logger.info(f"Encrypted: {filepath.name}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt_file(self, filepath: Path) -> Optional[Path]:
        """Decrypt a file"""
        if not self.fernet:
            logger.warning("Encryption not available")
            return None
        
        if not filepath.name.endswith('.enc'):
            logger.warning(f"Not an encrypted file: {filepath.name}")
            return None
        
        try:
            content = filepath.read_bytes()
            decrypted = self.fernet.decrypt(content)
            
            # Write decrypted file
            decrypted_path = filepath.with_suffix('')  # Remove .enc
            decrypted_path.write_bytes(decrypted)
            
            # Remove encrypted
            filepath.unlink()
            
            logger.info(f"Decrypted: {filepath.name}")
            return decrypted_path
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_string(self, text: str) -> Optional[str]:
        """Encrypt a string"""
        if not self.fernet:
            return None
        
        try:
            encrypted = self.fernet.encrypt(text.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"String encryption failed: {e}")
            return None
    
    def decrypt_string(self, encrypted_text: str) -> Optional[str]:
        """Decrypt a string"""
        if not self.fernet:
            return None
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"String decryption failed: {e}")
            return None
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        try:
            from cryptography.fernet import Fernet
            return Fernet.generate_key().decode()
        except ImportError:
            # Fallback: generate random key
            import secrets
            return secrets.token_urlsafe(32)
    
    @staticmethod
    def save_key(key: str, filepath: Path):
        """Save encryption key to file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(key, encoding='utf-8')
        filepath.chmod(0o600)  # Read/write for owner only
        logger.info(f"Encryption key saved to {filepath}")
    
    @staticmethod
    def load_key(filepath: Path) -> Optional[str]:
        """Load encryption key from file"""
        if not filepath.exists():
            return None
        return filepath.read_text().strip()
    
    def is_available(self) -> bool:
        """Check if encryption is available"""
        return self.fernet is not None
    
    def get_statistics(self) -> Dict:
        """Get encryption statistics"""
        return {
            "available": self.is_available(),
            "key_configured": self.key is not None,
            "key_file": str(self.key_file) if self.key_file else None,
        }


def create_encryption(
    key: Optional[str] = None,
    key_file: Optional[Path] = None
) -> VaultEncryption:
    """Create VaultEncryption instance"""
    return VaultEncryption(key=key, key_file=key_file)


def init_encryption(vault_path: Path) -> VaultEncryption:
    """Initialize encryption for vault"""
    key_file = vault_path / ".secrets" / "encryption.key"
    
    # Check if key exists
    if key_file.exists():
        key = VaultEncryption.load_key(key_file)
        if key:
            return VaultEncryption(key=key, key_file=key_file)
    
    # Generate new key
    key = VaultEncryption.generate_key()
    VaultEncryption.save_key(key, key_file)
    
    return VaultEncryption(key=key, key_file=key_file)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test encryption
    encryption = VaultEncryption(key="test-key-for-demo")
    
    if encryption.is_available():
        # Test string encryption
        original = "Secret message"
        encrypted = encryption.encrypt_string(original)
        decrypted = encryption.decrypt_string(encrypted)
        
        logger.info(f"Original: {original}")
        logger.info(f"Encrypted: {encrypted}")
        logger.info(f"Decrypted: {decrypted}")
        
        stats = encryption.get_statistics()
        logger.info(f"Statistics: {stats}")
