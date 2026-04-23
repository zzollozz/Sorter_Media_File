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


def _safe_copy(src: Path, dst: Path) -> None:
    """Copy file content only — no metadata. Works on SMB/gvfs mounts."""
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        shutil.copyfileobj(fsrc, fdst)


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
        _safe_copy(src, fallback)


def copy_video(src: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = _unique_path(dest_dir, src.stem, ".mp4")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        cmd = [
            "ffmpeg", "-i", str(src),
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", "libx264", "-preset", "slow", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-profile:v", "main", "-level", "4.0",
            "-c:a", "aac", "-ac", "2", "-ar", "44100", "-b:a", "128k",
            "-movflags", "+faststart",
            "-y", str(tmp_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and tmp_path.exists() and tmp_path.stat().st_size > 10_240:
            _safe_copy(tmp_path, dest_path)
            logger.info(f"Транскодированное видео: {src} -> {dest_path}")
        else:
            logger.error(f"ffmpeg неудача для {src}: {result.stderr[-300:]}")
            fallback = _unique_path(dest_dir, src.stem, src.suffix)
            _safe_copy(src, fallback)
    except FileNotFoundError:
        logger.error("ffmpeg не найден, копирую видео как есть")
        fallback = _unique_path(dest_dir, src.stem, src.suffix)
        _safe_copy(src, fallback)
    except Exception as e:
        logger.error(f"Видеокопирование не получилось {src}: {e}")
        fallback = _unique_path(dest_dir, src.stem, src.suffix)
        _safe_copy(src, fallback)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


def _dvd_fallback_copy(vob_parts: list[Path], dest_dir: Path, output_stem: str) -> None:
    largest = max(vob_parts, key=lambda p: p.stat().st_size)
    fallback_path = _unique_path(dest_dir, output_stem, ".vob")
    _safe_copy(largest, fallback_path)
    logger.warning(f"DVD fallback: скопирован наибольший VOB {largest} -> {fallback_path}")


def copy_dvd_titleset(vob_parts: list[Path], dest_dir: Path, output_stem: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = _unique_path(dest_dir, output_stem, ".mp4")
    concat_path: Path | None = None
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         delete=False, encoding="utf-8") as f:
            concat_path = Path(f.name)
            for vob in vob_parts:
                f.write(f"file '{vob.as_posix()}'\n")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_path),
            "-c:v", "libx264", "-preset", "slow", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-y", str(tmp_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and tmp_path.exists() and tmp_path.stat().st_size > 10_240:
            _safe_copy(tmp_path, dest_path)
            logger.info(
                f"DVD транскодирован: {vob_parts[0].parent} ({len(vob_parts)} VOB) -> {dest_path}"
            )
        else:
            logger.error(f"ffmpeg concat неудача для {output_stem}: {result.stderr[:500]}")
            _dvd_fallback_copy(vob_parts, dest_dir, output_stem)
    except FileNotFoundError:
        logger.error("ffmpeg не найден, копирую наибольший VOB как есть")
        _dvd_fallback_copy(vob_parts, dest_dir, output_stem)
    except Exception as e:
        logger.error(f"DVD транскодирование не получилось {output_stem}: {e}")
        _dvd_fallback_copy(vob_parts, dest_dir, output_stem)
    finally:
        if concat_path and concat_path.exists():
            concat_path.unlink()
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


def process_file(src: Path, file_type: str, dest_root: Path) -> None:
    if file_type == "image":
        copy_image(src, dest_root)
    elif file_type == "video":
        copy_video(src, dest_root)
