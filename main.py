import sys
from pathlib import Path

from loguru import logger
from tqdm import tqdm

from config import IGNORE_FILENAMES
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

    all_files = [p for p in source.rglob("*") if p.is_file()]
    total = len(all_files)
    print(f"Найдено файлов для обхода: {total}")

    processed = 0
    skipped = 0

    with tqdm(total=total, unit="файл", desc="Обработка", dynamic_ncols=True) as pbar:
        for file_path in all_files:
            pbar.set_postfix_str(file_path.name[:40])

            if file_path.name in IGNORE_FILENAMES:
                skipped += 1
                pbar.update(1)
                continue

            file_type = get_file_type(file_path)
            if file_type is None:
                logger.debug(f"Пропуск неподдерживаемого файла: {file_path}")
                skipped += 1
                pbar.update(1)
                continue

            date_str = get_creation_date(file_path)
            if date_str is None:
                logger.warning(f"Невозможно определить дату, пропуск: {file_path}")
                skipped += 1
                pbar.update(1)
                continue

            process_file(file_path, date_str, file_type, dest)
            processed += 1
            pbar.update(1)

    summary = f"Готово. Обработано: {processed}, Пропущено: {skipped}, Всего: {total}"
    logger.info(summary)
    print(f"\n{summary}")


if __name__ == "__main__":
    main()
