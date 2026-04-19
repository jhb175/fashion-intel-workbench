"""File storage service – Logo upload, thumbnail generation, and file download."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from app.utils.errors import ValidationError

# Allowed file formats and logo types
ALLOWED_FORMATS = {"png", "svg", "jpg", "jpeg"}
ALLOWED_LOGO_TYPES = {"main", "horizontal", "icon", "monochrome", "other"}

# Base upload directory (relative to project root)
UPLOAD_BASE_DIR = Path("uploads/logos")


class FileStorageService:
    """Manages file storage for brand logos."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or UPLOAD_BASE_DIR

    def validate_file_format(self, filename: str) -> str:
        """Validate and return the file extension (lowercase, without dot).

        Raises ``ValidationError`` if the format is not allowed.
        """
        if not filename or "." not in filename:
            raise ValidationError("文件名无效，缺少扩展名")

        ext = filename.rsplit(".", 1)[-1].lower()
        # Normalize jpeg → jpg for storage
        if ext == "jpeg":
            ext = "jpg"

        if ext not in ALLOWED_FORMATS:
            raise ValidationError(
                f"不支持的文件格式 '{ext}'，仅支持 {', '.join(sorted(ALLOWED_FORMATS - {'jpeg'}))}"
            )
        return ext

    def validate_logo_type(self, logo_type: str) -> str:
        """Validate logo_type and return it.

        Raises ``ValidationError`` if the type is not allowed.
        """
        if logo_type not in ALLOWED_LOGO_TYPES:
            raise ValidationError(
                f"不支持的 Logo 类型 '{logo_type}'，"
                f"仅支持 {', '.join(sorted(ALLOWED_LOGO_TYPES))}"
            )
        return logo_type

    async def save_upload(
        self,
        brand_id: uuid.UUID,
        filename: str,
        file_content: bytes,
    ) -> dict:
        """Save an uploaded file and generate a thumbnail.

        Returns a dict with file_path, thumbnail_path, file_format, file_size_bytes.
        """
        ext = self.validate_file_format(filename)

        # Build storage path: uploads/logos/{brand_id}/{uuid}.{ext}
        brand_dir = self.base_dir / str(brand_id)
        brand_dir.mkdir(parents=True, exist_ok=True)

        file_uuid = uuid.uuid4()
        stored_name = f"{file_uuid}.{ext}"
        file_path = brand_dir / stored_name

        # Write file
        file_path.write_bytes(file_content)

        # Generate thumbnail (simple copy for now; can be enhanced later)
        thumb_name = f"{file_uuid}_thumb.{ext}"
        thumb_path = brand_dir / thumb_name
        shutil.copy2(file_path, thumb_path)

        return {
            "file_path": str(file_path),
            "thumbnail_path": str(thumb_path),
            "file_format": ext,
            "file_size_bytes": len(file_content),
        }

    def delete_file(self, file_path: str) -> None:
        """Delete a file from disk if it exists."""
        p = Path(file_path)
        if p.exists():
            p.unlink()

        # Also try to delete the thumbnail (convention: *_thumb.ext)
        stem = p.stem
        ext = p.suffix
        parent = p.parent
        thumb_candidate = parent / f"{stem}_thumb{ext}"
        if thumb_candidate.exists():
            thumb_candidate.unlink()

    def get_file_path(self, file_path: str) -> Path:
        """Return the absolute Path for a stored file.

        Raises ``ValidationError`` if the file does not exist.
        """
        p = Path(file_path)
        if not p.exists():
            raise ValidationError("文件不存在")
        return p
