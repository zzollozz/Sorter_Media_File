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

## MCP Tools

### context7 — Library & Python Documentation
Use the `context7` MCP server to look up documentation for Python standard library and project dependencies **before writing code** — do not guess API signatures.

```
# Find the library ID first
mcp__context7__resolve-library-id  →  e.g. "loguru", "pillow", "exifread"

# Then fetch relevant docs
mcp__context7__query-docs  →  pass the resolved library ID + query
```

Use context7 when:
- Working with `loguru`, `Pillow`, `exifread`, `python-dateutil`
- Unsure about a Python stdlib module (pathlib, subprocess, datetime, shutil)
- Checking correct API before proposing code changes

## Error Workflow

When the program produces runtime errors, unexpected output, or test failures, use the **`error-fixer` agent**:

- Launch via: `Agent tool → subagent_type: error-fixer`
- Provide: the log excerpt or test output + description of expected vs actual behavior
- The agent will read `log_worker_media_sorter.log`, inspect source modules, diagnose root cause, and apply a fix

Do NOT manually re-run failing commands in a loop. Investigate root cause first.

## Architecture

The project follows a modular structure defined in `start_main_doca.md`:

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point, CLI argument parsing |
| `config.py` | Paths, date formats (`DD-MM-YYYY`), supported file extensions |
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
- **Target OS**: Debian 12 (avoid macOS-specific paths or APIs in production code).
- **Sensitive data**: Never hardcode credentials, API keys, tokens, or configurable paths in source files. Define them as environment variables in `.env` and load via `python-dotenv` (add to requirements if needed). Add `.env` to `.gitignore`.

## Dependencies

```
loguru==0.7.2
Pillow==10.0.1
exifread==3.0.0
python-dateutil==2.9.0
```

`ffmpeg` устанавливается в виртуальное окружение проекта (`.venv/`), не системно.

## Coding Standards

- **No shell=True**: always pass subprocess args as a list (already enforced in `copier.py`).
- **Path handling**: use `pathlib.Path` throughout — never string concatenation for paths.
- **Type hints**: all function signatures must include type hints (match existing code style).
- **No global state**: configuration lives in `config.py`; no module-level mutable globals.
- **Fallback safety**: if conversion fails (WebP, ffmpeg), fall back to raw `shutil.copy2()` — never silently drop files.
- **Tests required**: any new logic in `file_processor.py` or `copier.py` must have a corresponding test in `tests/`.
- **Unused dependencies**: `python-dateutil` is listed in requirements but not used — do not add new imports without using them.
- **ffmpeg**: not a pip package — must be installed as a system binary on Debian 12; verify presence before use (check `FileNotFoundError`).
