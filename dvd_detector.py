import re
from pathlib import Path

_VOB_CONTENT_RE = re.compile(r"^VTS_(\d{2})_([1-9]\d*)\.VOB$", re.IGNORECASE)


def find_dvd_folders(source: Path) -> list[Path]:
    return [p for p in source.rglob("*") if p.is_dir() and p.name.upper() == "VIDEO_TS"]


def group_content_vobs(video_ts_dir: Path) -> dict[int, list[Path]]:
    groups: dict[int, list[tuple[int, Path]]] = {}
    for vob in video_ts_dir.iterdir():
        m = _VOB_CONTENT_RE.match(vob.name)
        if m:
            title_num = int(m.group(1))
            part_num = int(m.group(2))
            groups.setdefault(title_num, []).append((part_num, vob))
    return {
        title: [path for _, path in sorted(parts)]
        for title, parts in sorted(groups.items())
    }


def dvd_output_stem(video_ts_dir: Path, title_num: int, total_titles: int) -> str:
    disc_name = video_ts_dir.parent.name
    if total_titles == 1:
        return disc_name
    return f"{disc_name}_VTS{title_num:02d}"
