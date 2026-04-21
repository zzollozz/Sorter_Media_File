import tempfile
import unittest
from pathlib import Path

from dvd_detector import dvd_output_stem, find_dvd_folders, group_content_vobs


class TestFindDvdFolders(unittest.TestCase):
    def test_finds_video_ts_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts = Path(tmpdir) / "MyDisc" / "VIDEO_TS"
            ts.mkdir(parents=True)
            result = find_dvd_folders(Path(tmpdir))
            self.assertEqual(result, [ts])

    def test_case_insensitive_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts = Path(tmpdir) / "disc" / "video_ts"
            ts.mkdir(parents=True)
            result = find_dvd_folders(Path(tmpdir))
            self.assertEqual(len(result), 1)

    def test_no_dvd_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "photos").mkdir()
            result = find_dvd_folders(Path(tmpdir))
            self.assertEqual(result, [])


class TestGroupContentVobs(unittest.TestCase):
    def _setup_vts(self, tmpdir: Path) -> None:
        files = [
            "VIDEO_TS.VOB", "VIDEO_TS.IFO", "VIDEO_TS.BUP",
            "VTS_01_0.VOB", "VTS_01_0.IFO", "VTS_01_0.BUP",
            "VTS_01_1.VOB", "VTS_01_2.VOB",
            "VTS_02_0.VOB", "VTS_02_0.IFO", "VTS_02_0.BUP",
            "VTS_02_1.VOB",
        ]
        for f in files:
            (tmpdir / f).touch()

    def test_groups_content_vobs_by_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts = Path(tmpdir)
            self._setup_vts(ts)
            groups = group_content_vobs(ts)
            self.assertIn(1, groups)
            self.assertIn(2, groups)
            self.assertEqual(len(groups[1]), 2)
            self.assertEqual(len(groups[2]), 1)

    def test_menu_vobs_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts = Path(tmpdir)
            self._setup_vts(ts)
            groups = group_content_vobs(ts)
            for parts in groups.values():
                for p in parts:
                    self.assertNotIn("_0.VOB", p.name.upper())

    def test_parts_sorted_by_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts = Path(tmpdir)
            for i in [3, 1, 2]:
                (ts / f"VTS_01_{i}.VOB").touch()
            groups = group_content_vobs(ts)
            names = [p.name for p in groups[1]]
            self.assertEqual(names, ["VTS_01_1.VOB", "VTS_01_2.VOB", "VTS_01_3.VOB"])

    def test_ifo_and_bup_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts = Path(tmpdir)
            (ts / "VTS_01_0.IFO").touch()
            (ts / "VTS_01_0.BUP").touch()
            (ts / "VTS_01_1.VOB").touch()
            groups = group_content_vobs(ts)
            self.assertEqual(len(groups), 1)
            self.assertEqual(len(groups[1]), 1)

    def test_empty_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            groups = group_content_vobs(Path(tmpdir))
            self.assertEqual(groups, {})


class TestDvdOutputStem(unittest.TestCase):
    def test_single_title_no_vts_suffix(self):
        video_ts = Path("/media/первый звонок DVD/VIDEO_TS")
        stem = dvd_output_stem(video_ts, 1, 1)
        self.assertEqual(stem, "первый звонок DVD")

    def test_multiple_titles_appends_vts_number(self):
        video_ts = Path("/media/первый звонок DVD/VIDEO_TS")
        stem = dvd_output_stem(video_ts, 2, 3)
        self.assertEqual(stem, "первый звонок DVD_VTS02")

    def test_title_num_zero_padded(self):
        video_ts = Path("/media/disc/VIDEO_TS")
        stem = dvd_output_stem(video_ts, 5, 10)
        self.assertEqual(stem, "disc_VTS05")


if __name__ == "__main__":
    unittest.main()
