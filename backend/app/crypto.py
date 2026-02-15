from cryptography.fernet import Fernet
from .config import settings

_fernet = Fernet(settings.encryption_key.encode())


def encrypt_token(token: str) -> str:
    """Encrypt a refresh token using Fernet"""
    return _fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a refresh token using Fernet"""
    return _fernet.decrypt(encrypted_token.encode()).decode()
