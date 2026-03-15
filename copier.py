import shutil
import subprocess
from pathlib import Path

from loguru import logger
from PIL import Image

from config import FOTO_SUBDIR, VIDEO_SUBDIR


def _unique_path(dest_dir: Path, stem: str, suffix: str) -> Path:
    dest = dest_dir / f"{stem}{suffix}"
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return dest


def copy_image(src: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = _unique_path(dest_dir, src.stem, ".webp")
    try:
        with Image.open(src) as img:
            img.save(dest_path, "WEBP", quality=85)
        logger.info(f"Конвертированное изображение: {src} -> {dest_path}")
    except Exception as e:
        logger.error(f"Конвертация изображения не удалась для {src}: {e}, copying as-is")
        fallback = _unique_path(dest_dir, src.stem, src.suffix)
        shutil.copy2(src, fallback)


def copy_video(src: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = _unique_path(dest_dir, src.stem, ".mp4")
    cmd = [
        "ffmpeg", "-i", str(src),
        "-c:v", "libx264", "-preset", "slow", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-y", str(dest_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"ffmpeg неудача для {src}: {result.stderr}")
            fallback = _unique_path(dest_dir, src.stem, src.suffix)
            shutil.copy2(src, fallback)
        else:
            logger.info(f"Транскодированное видео: {src} -> {dest_path}")
    except FileNotFoundError:
        logger.error("ffmpeg не найден, копирую видео как есть")
        fallback = _unique_path(dest_dir, src.stem, src.suffix)
        shutil.copy2(src, fallback)
    except Exception as e:
        logger.error(f"Видеокопирование не получилось {src}: {e}")
        fallback = _unique_path(dest_dir, src.stem, src.suffix)
        shutil.copy2(src, fallback)


def process_file(src: Path, date_str: str, file_type: str, dest_root: Path) -> None:
    dest_dir = dest_root / date_str / file_type
    if file_type == FOTO_SUBDIR:
        copy_image(src, dest_dir)
    elif file_type == VIDEO_SUBDIR:
        copy_video(src, dest_dir)