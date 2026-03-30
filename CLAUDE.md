# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 3.11 media converter that recursively traverses a source directory and copies/converts files directly into the target directory (flat structure, no subfolders).

Target path format: `<dest>/file_name.webp` or `<dest>/file_name.mp4`

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
- Working with `loguru`, `Pillow`, `python-dateutil`
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
| `config.py` | Supported file extensions, log file name |
| `file_processor.py` | File type detection (image/video) |
| `copier.py` | File copying; image conversion to WebP (`Pillow`); video transcoding to H.264 via `subprocess` + `ffmpeg` |
| `logger_setup.py` | `loguru` config: all actions to `log_worker_media_sorter.log`, only critical errors to console |
| `tests/` | `unittest`-based unit and integration tests for `file_processor` and `copier` |

## Key Rules

- **Virtual environment**: all dependencies install into `.venv/` in the project root; never install globally.
- **Source directory is read-only** — never write to source dir A.
- **subprocess + ffmpeg**: use list-form args (never shell=True with user input) to avoid injection.
- **Logging**: use `loguru`; log file = `log_worker_media_sorter.log`; console output = CRITICAL only.
- **Target OS**: Debian 12 (avoid macOS-specific paths or APIs in production code).
- **Sensitive data**: Never hardcode credentials, API keys, tokens, or configurable paths in source files. Define them as environment variables in `.env` and load via `python-dotenv` (add to requirements if needed). Add `.env` to `.gitignore`.

## Dependencies

```
loguru==0.7.2
Pillow==10.0.1
python-dateutil==2.9.0
tqdm>=4.65.0
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
- **Progress bar**: `tqdm` is used in `main.py` for terminal progress display; requires pre-collecting all files into a list first (for `total` count).
- **Completion notification**: print() is called at the end of `main()` with summary stats — not logger, since stderr sink is CRITICAL-only.
- **Unsupported formats**: System files (`Thumbs.db`, `.DS_Store`, `desktop.ini`) are skipped silently via `IGNORE_FILENAMES` in `config.py`. RAW camera formats (`.cr2`, `.nef`, `.arw`, `.dng`, `.raf`, `.orf`, `.rw2`) are in `IMAGE_EXTENSIONS`; Pillow cannot convert them → fallback `shutil.copy2()` runs automatically.
