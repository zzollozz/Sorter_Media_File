IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".tiff", ".tif", ".heic", ".heif", ".webp",
    # RAW-форматы камер (при неудаче конвертации копируются как есть)
    ".cr2", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2",
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv",
    ".flv", ".m4v", ".3gp", ".mts", ".m2ts", ".ts",
}

# Системные файлы ОС — пропускаются без записи в лог
IGNORE_FILENAMES = {"Thumbs.db", "thumbs.db", ".DS_Store", "desktop.ini"}

LOG_FILE = "log_worker_media_sorter.log"
