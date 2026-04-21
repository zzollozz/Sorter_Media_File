import sys
from pathlib import Path

from loguru import logger
from tqdm import tqdm

from config import IGNORE_FILENAMES
from copier import copy_dvd_titleset, process_file
from dvd_detector import dvd_output_stem, find_dvd_folders, group_content_vobs
from file_processor import get_file_type
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

    dvd_processed_dirs: set[Path] = set()
    dvd_folders = find_dvd_folders(source)
    if dvd_folders:
        logger.info(f"Найдено DVD папок: {len(dvd_folders)}")
        print(f"Найдено DVD VIDEO_TS папок: {len(dvd_folders)}")
    for video_ts_dir in dvd_folders:
        groups = group_content_vobs(video_ts_dir)
        total_titles = len(groups)
        if total_titles == 0:
            logger.warning(f"VIDEO_TS без контентных VOB: {video_ts_dir}")
            dvd_processed_dirs.add(video_ts_dir)
            continue
        for title_num, vob_parts in groups.items():
            stem = dvd_output_stem(video_ts_dir, title_num, total_titles)
            copy_dvd_titleset(vob_parts, dest, stem)
            processed += 1
        dvd_processed_dirs.add(video_ts_dir)
        skipped += sum(1 for f in video_ts_dir.rglob("*") if f.is_file())

    all_files = [p for p in source.rglob("*") if p.is_file()]
    total = len(all_files)
    print(f"Найдено файлов для обхода: {total}")

    with tqdm(total=total, unit="файл", desc="Обработка", dynamic_ncols=True) as pbar:
        for file_path in all_files:
            pbar.set_postfix_str(file_path.name[:40])

            if dvd_processed_dirs and any(d in file_path.parents for d in dvd_processed_dirs):
                pbar.update(1)
                continue

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

            process_file(file_path, file_type, dest)
            processed += 1
            pbar.update(1)

    summary = f"Готово. Обработано: {processed}, Пропущено: {skipped}, Всего: {total}"
    logger.info(summary)
    print(f"\n{summary}")


if __name__ == "__main__":
    main()
