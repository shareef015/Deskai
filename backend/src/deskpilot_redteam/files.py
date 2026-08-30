from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re


class MaliciousFileViolation(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class UploadMetadata:
    filename: str
    declared_mime: str
    size_bytes: int
    archive_entries: int = 0
    uncompressed_bytes: int = 0


@dataclass(frozen=True, slots=True)
class SafeFilePolicy:
    max_bytes: int = 10 * 1024 * 1024
    max_archive_entries: int = 200
    max_archive_ratio: float = 20.0
    allowed_extensions: frozenset[str] = frozenset({".txt", ".md", ".pdf", ".png", ".jpg", ".jpeg", ".json"})
    allowed_mimes: frozenset[str] = frozenset({
        "text/plain",
        "text/markdown",
        "application/pdf",
        "image/png",
        "image/jpeg",
        "application/json",
    })

    def validate(self, metadata: UploadMetadata, *, archive_paths: tuple[str, ...] = ()) -> None:
        if metadata.size_bytes <= 0 or metadata.size_bytes > self.max_bytes:
            raise MaliciousFileViolation("file_size_denied")
        if "\x00" in metadata.filename or re.search(r"[\r\n]", metadata.filename):
            raise MaliciousFileViolation("unsafe_filename")
        path = PurePosixPath(metadata.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise MaliciousFileViolation("path_traversal")
        suffix = path.suffix.lower()
        if suffix not in self.allowed_extensions:
            raise MaliciousFileViolation("extension_denied")
        if metadata.declared_mime.lower() not in self.allowed_mimes:
            raise MaliciousFileViolation("mime_denied")
        if suffix in {".exe", ".dll", ".ps1", ".bat", ".cmd", ".js", ".vbs", ".msi", ".docm", ".xlsm"}:
            raise MaliciousFileViolation("active_content_denied")
        if metadata.archive_entries > self.max_archive_entries:
            raise MaliciousFileViolation("archive_entry_limit")
        if metadata.uncompressed_bytes:
            ratio = metadata.uncompressed_bytes / max(metadata.size_bytes, 1)
            if ratio > self.max_archive_ratio:
                raise MaliciousFileViolation("archive_expansion_ratio")
        for entry in archive_paths:
            member = PurePosixPath(entry.replace("\\", "/"))
            if member.is_absolute() or ".." in member.parts:
                raise MaliciousFileViolation("archive_path_traversal")
