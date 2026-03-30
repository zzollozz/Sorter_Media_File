from pathlib import Path

from config import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


def get_file_type(file_path: Path) -> str | None:
    ext = file_path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return None
