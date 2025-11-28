"""
Encryption utilities for secure token storage.
Uses Fernet symmetric encryption to protect sensitive OAuth tokens.
"""

from cryptography.fernet import Fernet
from config import settings


def _get_cipher() -> Fernet:
    """
    Get Fernet cipher instance using encryption key from settings.

    Returns:
        Fernet: Cipher instance for encryption/decryption

    Raises:
        ValueError: If encryption key is not configured
    """
    if not settings.ENCRYPTION_KEY:
        raise ValueError(
            "ENCRYPTION_KEY not configured. "
            "Generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    # Ensure key is bytes
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()

    return Fernet(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for secure storage.

    Args:
        token: Plain text token to encrypt

    Returns:
        str: Encrypted token as base64 string

    Example:
        >>> encrypted = encrypt_token("my_secret_token")
        >>> print(encrypted)
        'gAAAAABh...'
    """
    cipher = _get_cipher()
    encrypted_bytes = cipher.encrypt(token.encode())
    return encrypted_bytes.decode()


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt a previously encrypted token.

    Args:
        encrypted: Encrypted token as base64 string

    Returns:
        str: Decrypted plain text token

    Raises:
        cryptography.fernet.InvalidToken: If token is invalid or corrupted

    Example:
        >>> decrypted = decrypt_token(encrypted_token)
        >>> print(decrypted)
        'my_secret_token'
    """
    cipher = _get_cipher()
    decrypted_bytes = cipher.decrypt(encrypted.encode())
    return decrypted_bytes.decode()
