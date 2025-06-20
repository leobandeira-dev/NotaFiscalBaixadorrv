"""
Email Password Encryption System
Provides reversible encryption for email passwords (unlike password hashing which is one-way)
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EmailPasswordEncryption:
    def __init__(self):
        # Get encryption key from environment or generate one
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Get encryption key from environment or generate a new one"""
        # In production, this should be stored securely (environment variable)
        secret_key = os.environ.get('EMAIL_ENCRYPTION_KEY')
        
        if not secret_key:
            # Generate a key based on a master password
            master_password = os.environ.get('SESSION_SECRET', 'default-master-key').encode()
            salt = b'email_encryption_salt'  # In production, use a random salt
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password))
            return key
        
        return secret_key.encode()
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password for storage"""
        if not password:
            return ""
        
        encrypted = self.fernet.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password for use"""
        if not encrypted_password:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting password: {e}")
            return ""
    
    def is_encrypted(self, password_string: str) -> bool:
        """Check if a string appears to be an encrypted password"""
        try:
            # Try to decode as base64 and check length
            decoded = base64.urlsafe_b64decode(password_string.encode())
            return len(decoded) > 20  # Encrypted passwords are longer
        except:
            return False

# Global instance
email_crypto = EmailPasswordEncryption()

def encrypt_email_password(password: str) -> str:
    """Convenience function to encrypt email password"""
    return email_crypto.encrypt_password(password)

def decrypt_email_password(encrypted_password: str) -> str:
    """Convenience function to decrypt email password"""
    return email_crypto.decrypt_password(encrypted_password)