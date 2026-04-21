import shutil
import subprocess
import tempfile
from pathlib import Path

from loguru import logger
from PIL import Image


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


def _dvd_fallback_copy(vob_parts: list[Path], dest_dir: Path, output_stem: str) -> None:
    largest = max(vob_parts, key=lambda p: p.stat().st_size)
    fallback_path = _unique_path(dest_dir, output_stem, ".vob")
    shutil.copy2(largest, fallback_path)
    logger.warning(f"DVD fallback: скопирован наибольший VOB {largest} -> {fallback_path}")


def copy_dvd_titleset(vob_parts: list[Path], dest_dir: Path, output_stem: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = _unique_path(dest_dir, output_stem, ".mp4")
    concat_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         delete=False, encoding="utf-8") as f:
            concat_path = Path(f.name)
            for vob in vob_parts:
                f.write(f"file '{vob.as_posix()}'\n")
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_path),
            "-c:v", "libx264", "-preset", "slow", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-y", str(dest_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"ffmpeg concat неудача для {output_stem}: {result.stderr[:500]}")
            _dvd_fallback_copy(vob_parts, dest_dir, output_stem)
        else:
            logger.info(
                f"DVD транскодирован: {vob_parts[0].parent} ({len(vob_parts)} VOB) -> {dest_path}"
            )
    except FileNotFoundError:
        logger.error("ffmpeg не найден, копирую наибольший VOB как есть")
        _dvd_fallback_copy(vob_parts, dest_dir, output_stem)
    except Exception as e:
        logger.error(f"DVD транскодирование не получилось {output_stem}: {e}")
        _dvd_fallback_copy(vob_parts, dest_dir, output_stem)
    finally:
        if concat_path and concat_path.exists():
            concat_path.unlink()


def process_file(src: Path, file_type: str, dest_root: Path) -> None:
    if file_type == "image":
        copy_image(src, dest_root)
    elif file_type == "video":
        copy_video(src, dest_root)
