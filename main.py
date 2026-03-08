import sys
from pathlib import Path

from loguru import logger

from copier import process_file
from file_processor import get_creation_date, get_file_type
from logger_setup import setup_logger


def main() -> None:
    if len(sys.argv) != 3:
        print("Использование: python3 main.py <source_dir> <dest_dir>")
        sys.exit(1)

    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])

    if not source.is_dir():
        print(f"Каталог исходников не найден: {source}")
        sys.exit(1)

    setup_logger()
    logger.info(f"Стартовая сортировка медиа: {source} -> {dest}")

    processed = 0
    skipped = 0

    for file_path in source.rglob("*"):
        if not file_path.is_file():
            continue

        file_type = get_file_type(file_path)
        if file_type is None:
            logger.debug(f"Пропуск неподдерживаемого файла: {file_path}")
            skipped += 1
            continue

        date_str = get_creation_date(file_path)
        if date_str is None:
            logger.warning(f"Невозможно определить дату, пропуск: {file_path}")
            skipped += 1
            continue

        process_file(file_path, date_str, file_type, dest)
        processed += 1

    logger.info(f"Готово. Обработка: {processed}, Пропущено: {skipped}")


if __name__ == "__main__":
    main()