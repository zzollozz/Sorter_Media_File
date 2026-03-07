# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 3.11 media sorter that recursively traverses a source directory, extracts creation dates from media file EXIF metadata, and copies/converts files into a structured target directory sorted by date and type.

Target path format: `<dest>/DD-MM-YYYY/foto/` or `<dest>/DD-MM-YYYY/video/`

## Commands

```bash
# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (always into .venv)
pip install -r requirements.txt

# Run the sorter
python3 main.py <source_dir> <dest_dir>

# Run all tests
python -m unittest discover -s tests
```

## Architecture

The project follows a modular structure defined in `start_main_doca.md`:

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point, CLI argument parsing |
| `config.py` | Paths, date formats (`DD-MM_YYYY`), supported file extensions |
| `file_processor.py` | EXIF metadata extraction (`exifread`), file type detection (photo/video) |
| `copier.py` | File copying; image conversion to WebP (`Pillow`); video transcoding to H.265 via `subprocess` + `ffmpeg` |
| `logger_setup.py` | `loguru` config: all actions to `log_worker_media_sorter.log`, only critical errors to console |
| `tests/` | `unittest`-based unit and integration tests for `file_processor` and `copier` |

## Key Rules

- **Virtual environment**: all dependencies install into `.venv/` in the project root; never install globally.
- **Source directory is read-only** — never write to source dir A.
- **subprocess + ffmpeg**: use list-form args (never shell=True with user input) to avoid injection.
- **Logging**: use `loguru`; log file = `log_worker_media_sorter.log`; console output = CRITICAL only.
- **Date format**: folder names must be `DD-MM-YYYY` (e.g., `15-05-2024`).
- **File types**: subfolders named `foto` (images) and `video` (video) — not "photo".
- **Target OS**: Debian 12 (avoid macOS-specific paths or APIs in production code).

## Dependencies

```
loguru==0.7.2
Pillow==10.0.1
exifread==3.0.0
python-dateutil==2.9.0
```

`ffmpeg` устанавливается в виртуальное окружение проекта (`.venv/`), не системно.
