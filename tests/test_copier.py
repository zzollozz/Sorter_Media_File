import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from copier import copy_dvd_titleset, copy_image, copy_video, process_file


class TestCopyImage(unittest.TestCase):
    def _make_jpeg(self, path: Path) -> None:
        from PIL import Image
        img = Image.new("RGB", (10, 10), color=(255, 0, 0))
        img.save(path, "JPEG")

    def test_converts_to_webp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "test.jpg"
            dest_dir = Path(tmpdir) / "dest"
            self._make_jpeg(src)

            copy_image(src, dest_dir)

            webp_files = list(dest_dir.glob("*.webp"))
            self.assertEqual(len(webp_files), 1)
            self.assertEqual(webp_files[0].stem, "test")

    def test_dest_dir_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "test.jpg"
            dest_dir = Path(tmpdir) / "new" / "nested"
            self._make_jpeg(src)

            copy_image(src, dest_dir)
            self.assertTrue(dest_dir.exists())

    def test_name_collision_handled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "test.jpg"
            dest_dir = Path(tmpdir) / "dest"
            self._make_jpeg(src)

            copy_image(src, dest_dir)
            copy_image(src, dest_dir)

            webp_files = sorted(dest_dir.glob("*.webp"))
            self.assertEqual(len(webp_files), 2)


class TestCopyVideo(unittest.TestCase):
    @patch("copier.subprocess.run")
    def test_ffmpeg_called_with_list_args(self, mock_run):
        mock_run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "clip.mp4"
            src.touch()
            dest_dir = Path(tmpdir) / "dest"

            copy_video(src, dest_dir)

            args = mock_run.call_args[0][0]
            self.assertIsInstance(args, list)
            self.assertEqual(args[0], "ffmpeg")

    @patch("copier.subprocess.run")
    def test_fallback_copy_on_ffmpeg_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "error"
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "clip.mp4"
            src.write_bytes(b"fake video")
            dest_dir = Path(tmpdir) / "dest"

            copy_video(src, dest_dir)

            self.assertTrue(any(dest_dir.iterdir()))

    @patch("copier.subprocess.run")
    def test_ffmpeg_uses_h264_and_faststart(self, mock_run):
        mock_run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "clip.mp4"
            src.touch()
            dest_dir = Path(tmpdir) / "dest"
            copy_video(src, dest_dir)
            args = mock_run.call_args[0][0]
            self.assertIn("libx264", args)
            self.assertIn("+faststart", args)


class TestCopyDvdTitleset(unittest.TestCase):
    def _make_vobs(self, tmpdir: Path, count: int = 2) -> list[Path]:
        vobs = []
        for i in range(1, count + 1):
            p = tmpdir / f"VTS_01_{i}.VOB"
            p.write_bytes(b"x" * (i * 100))
            vobs.append(p)
        return vobs

    @patch("copier.subprocess.run")
    def test_ffmpeg_called_with_concat_demuxer(self, mock_run):
        mock_run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            vobs = self._make_vobs(tmp)
            dest_dir = tmp / "dest"
            copy_dvd_titleset(vobs, dest_dir, "MyDisc_VTS01")
            args = mock_run.call_args[0][0]
            self.assertIsInstance(args, list)
            self.assertEqual(args[0], "ffmpeg")
            self.assertIn("concat", args)

    @patch("copier.subprocess.run")
    def test_args_are_list_not_shell(self, mock_run):
        mock_run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            vobs = self._make_vobs(tmp)
            copy_dvd_titleset(vobs, tmp / "dest", "MyDisc")
            kwargs = mock_run.call_args[1]
            self.assertNotEqual(kwargs.get("shell"), True)

    @patch("copier.subprocess.run")
    def test_concat_list_file_deleted_after_success(self, mock_run):
        created_concat: list[str] = []

        def capturing_run(args, **kwargs):
            i_idx = args.index("-i")
            created_concat.append(args[i_idx + 1])
            return mock_run.return_value

        mock_run.side_effect = capturing_run
        mock_run.return_value.returncode = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            vobs = self._make_vobs(tmp)
            copy_dvd_titleset(vobs, tmp / "dest", "MyDisc")

        self.assertEqual(len(created_concat), 1)
        self.assertFalse(Path(created_concat[0]).exists())

    @patch("copier.subprocess.run")
    def test_fallback_copies_largest_vob_on_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "encode error"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            vob1 = tmp / "VTS_01_1.VOB"
            vob2 = tmp / "VTS_01_2.VOB"
            vob1.write_bytes(b"x" * 10)
            vob2.write_bytes(b"x" * 9999)
            dest_dir = tmp / "dest"
            copy_dvd_titleset([vob1, vob2], dest_dir, "MyDisc_VTS01")
            vob_files = list(dest_dir.glob("*.vob"))
            self.assertEqual(len(vob_files), 1)
            self.assertEqual(vob_files[0].stat().st_size, 9999)

    @patch("copier.subprocess.run")
    def test_output_mp4_uses_provided_stem(self, mock_run):
        mock_run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            vobs = self._make_vobs(tmp)
            copy_dvd_titleset(vobs, tmp / "dest", "первый звонок DVD_VTS01")
            args = mock_run.call_args[0][0]
            self.assertIn("первый звонок DVD_VTS01", args[-1])
            self.assertTrue(args[-1].endswith(".mp4"))

    def test_fallback_on_ffmpeg_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            vob1 = tmp / "VTS_01_1.VOB"
            vob1.write_bytes(b"content")
            dest_dir = tmp / "dest"
            with patch("copier.subprocess.run", side_effect=FileNotFoundError):
                copy_dvd_titleset([vob1], dest_dir, "MyDisc")
            self.assertTrue(any(dest_dir.iterdir()))


class TestProcessFile(unittest.TestCase):
    @patch("copier.copy_image")
    def test_image_calls_copy_image(self, mock_copy):
        process_file(Path("test.jpg"), "image", Path("/dest"))
        mock_copy.assert_called_once_with(Path("test.jpg"), Path("/dest"))

    @patch("copier.copy_video")
    def test_video_calls_copy_video(self, mock_copy):
        process_file(Path("test.mp4"), "video", Path("/dest"))
        mock_copy.assert_called_once_with(Path("test.mp4"), Path("/dest"))


if __name__ == "__main__":
    unittest.main()
