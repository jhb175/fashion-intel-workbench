"""Encryption service for secure API Key storage using Fernet symmetric encryption."""

from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    """API Key 加密服务

    Uses Fernet symmetric encryption to encrypt, decrypt, and mask API keys.
    The encryption key should be provided from environment variables via settings.
    """

    def __init__(self, encryption_key: str) -> None:
        """Initialize the Fernet cipher with the given encryption key.

        Args:
            encryption_key: A URL-safe base64-encoded 32-byte key for Fernet.

        Raises:
            ValueError: If the encryption key is invalid or cannot be used
                to create a Fernet cipher.
        """
        try:
            self._fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception as exc:
            raise ValueError(f"Invalid encryption key: {exc}") from exc

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext and return the ciphertext as a UTF-8 string.

        Args:
            plaintext: The plain text string to encrypt.

        Returns:
            The encrypted ciphertext as a UTF-8 string.
        """
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext and return the original plaintext string.

        Args:
            ciphertext: The encrypted string to decrypt.

        Returns:
            The original plaintext string.

        Raises:
            InvalidToken: If the ciphertext is invalid or was encrypted
                with a different key.
        """
        return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """Mask an API key for safe display.

        Shows the first 3 characters and last 4 characters with **** in between.
        For very short keys (fewer than 7 characters), masks everything with ****.

        Examples:
            "sk-abc123xyz7890" -> "sk-****...****7890"
            "short" -> "****"

        Args:
            api_key: The API key to mask.

        Returns:
            The masked API key string.
        """
        if len(api_key) < 7:
            return "****"
        return f"{api_key[:3]}****...****{api_key[-4:]}"
