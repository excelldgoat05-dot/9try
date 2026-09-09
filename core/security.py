from cryptography.fernet import Fernet
from core.config import settings
import base64
import hashlib

def get_fernet() -> Fernet:
    # Derive a Fernet key from the ENCRYPTION_KEY (simple but effective)
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

def encrypt_data(data: str) -> str:
    f = get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
