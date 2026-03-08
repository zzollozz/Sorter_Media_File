from datetime import datetime
from pathlib import Path

import exifread
from loguru import logger

from config import DATE_FORMAT, FOTO_SUBDIR, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, VIDEO_SUBDIR


def get_file_type(file_path: Path) -> str | None:
    ext = file_path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return FOTO_SUBDIR
    if ext in VIDEO_EXTENSIONS:
        return VIDEO_SUBDIR
    return None


def get_creation_date(file_path: Path) -> str | None:
    try:
        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal", details=False)
        for tag in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            if tag in tags:
                dt = datetime.strptime(str(tags[tag]), "%Y:%m:%d %H:%M:%S")
                return dt.strftime(DATE_FORMAT)
    except Exception as e:
        logger.warning(f"EXIF прочитал неудачно {file_path}: {e}")

    try:
        mtime = file_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        logger.warning(f"Без EXIF-даты, использую mtime для {file_path}")
        return dt.strftime(DATE_FORMAT)
    except Exception as e:
        logger.error(f"Не могу найти дату {file_path}: {e}")
        return None