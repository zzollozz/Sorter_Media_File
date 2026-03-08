import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from copier import copy_image, copy_video, process_file


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


class TestProcessFile(unittest.TestCase):
    @patch("copier.copy_image")
    def test_foto_calls_copy_image(self, mock_copy):
        process_file(Path("test.jpg"), "15-05-2024", "foto", Path("/dest"))
        mock_copy.assert_called_once_with(Path("test.jpg"), Path("/dest/15-05-2024/foto"))

    @patch("copier.copy_video")
    def test_video_calls_copy_video(self, mock_copy):
        process_file(Path("test.mp4"), "15-05-2024", "video", Path("/dest"))
        mock_copy.assert_called_once_with(Path("test.mp4"), Path("/dest/15-05-2024/video"))


if __name__ == "__main__":
    unittest.main()