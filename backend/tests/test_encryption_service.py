"""Unit tests for the EncryptionService."""

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.services.encryption_service import EncryptionService


@pytest.fixture
def encryption_key() -> str:
    """Generate a valid Fernet key for testing."""
    return Fernet.generate_key().decode("utf-8")


@pytest.fixture
def service(encryption_key: str) -> EncryptionService:
    """Create an EncryptionService instance with a valid key."""
    return EncryptionService(encryption_key)


class TestEncryptionServiceInit:
    """Tests for EncryptionService initialization."""

    def test_valid_key(self, encryption_key: str) -> None:
        svc = EncryptionService(encryption_key)
        assert svc is not None

    def test_invalid_key_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid encryption key"):
            EncryptionService("not-a-valid-fernet-key")

    def test_empty_key_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid encryption key"):
            EncryptionService("")


class TestEncryptDecrypt:
    """Tests for encrypt and decrypt round-trip."""

    def test_round_trip(self, service: EncryptionService) -> None:
        plaintext = "sk-abc123secretkey"
        ciphertext = service.encrypt(plaintext)
        assert service.decrypt(ciphertext) == plaintext

    def test_ciphertext_differs_from_plaintext(self, service: EncryptionService) -> None:
        plaintext = "sk-abc123secretkey"
        ciphertext = service.encrypt(plaintext)
        assert ciphertext != plaintext

    def test_encrypt_empty_string(self, service: EncryptionService) -> None:
        ciphertext = service.encrypt("")
        assert service.decrypt(ciphertext) == ""

    def test_encrypt_unicode(self, service: EncryptionService) -> None:
        plaintext = "密钥-テスト-🔑"
        ciphertext = service.encrypt(plaintext)
        assert service.decrypt(ciphertext) == plaintext

    def test_decrypt_with_wrong_key_raises(self, service: EncryptionService) -> None:
        ciphertext = service.encrypt("secret")
        other_key = Fernet.generate_key().decode("utf-8")
        other_service = EncryptionService(other_key)
        with pytest.raises(InvalidToken):
            other_service.decrypt(ciphertext)

    def test_decrypt_invalid_ciphertext_raises(self, service: EncryptionService) -> None:
        with pytest.raises(Exception):
            service.decrypt("not-valid-ciphertext")


class TestMaskApiKey:
    """Tests for the static mask_api_key method."""

    def test_normal_key(self) -> None:
        assert EncryptionService.mask_api_key("sk-abc123xyz7890") == "sk-****...****7890"

    def test_exactly_seven_chars(self) -> None:
        result = EncryptionService.mask_api_key("1234567")
        assert result == "123****...****4567"

    def test_short_key_masked_completely(self) -> None:
        assert EncryptionService.mask_api_key("short") == "****"

    def test_six_char_key_masked_completely(self) -> None:
        assert EncryptionService.mask_api_key("abcdef") == "****"

    def test_single_char_key(self) -> None:
        assert EncryptionService.mask_api_key("a") == "****"

    def test_empty_key(self) -> None:
        assert EncryptionService.mask_api_key("") == "****"

    def test_long_key_preserves_prefix_suffix(self) -> None:
        key = "sk-" + "x" * 50 + "a1b2"
        result = EncryptionService.mask_api_key(key)
        assert result.startswith("sk-")
        assert result.endswith("a1b2")
        assert "****...****" in result
