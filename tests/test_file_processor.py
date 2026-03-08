import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from file_processor import get_creation_date, get_file_type


class TestGetFileType(unittest.TestCase):
    def test_jpg_returns_foto(self):
        self.assertEqual(get_file_type(Path("photo.jpg")), "foto")

    def test_jpeg_uppercase_returns_foto(self):
        self.assertEqual(get_file_type(Path("photo.JPEG")), "foto")

    def test_png_returns_foto(self):
        self.assertEqual(get_file_type(Path("image.png")), "foto")

    def test_mp4_returns_video(self):
        self.assertEqual(get_file_type(Path("clip.mp4")), "video")

    def test_mov_uppercase_returns_video(self):
        self.assertEqual(get_file_type(Path("clip.MOV")), "video")

    def test_mkv_returns_video(self):
        self.assertEqual(get_file_type(Path("clip.mkv")), "video")

    def test_pdf_returns_none(self):
        self.assertIsNone(get_file_type(Path("doc.pdf")))

    def test_txt_returns_none(self):
        self.assertIsNone(get_file_type(Path("readme.txt")))

    def test_no_extension_returns_none(self):
        self.assertIsNone(get_file_type(Path("noextension")))


class TestGetCreationDate(unittest.TestCase):
    @patch("file_processor.exifread.process_file")
    @patch("builtins.open", new_callable=mock_open)
    def test_exif_date_extracted(self, mock_file, mock_exif):
        tag_mock = MagicMock()
        tag_mock.__str__ = lambda s: "2024:05:15 10:30:00"
        mock_exif.return_value = {"EXIF DateTimeOriginal": tag_mock}

        result = get_creation_date(Path("test.jpg"))
        self.assertEqual(result, "15-05-2024")

    @patch("file_processor.exifread.process_file", return_value={})
    @patch("builtins.open", new_callable=mock_open)
    @patch("file_processor.Path.stat")
    def test_fallback_to_mtime(self, mock_stat, _mock_file, _mock_exif):
        # 2024-05-15 00:00:00 UTC
        mock_stat.return_value.st_mtime = 1715731200.0
        result = get_creation_date(Path("test.jpg"))
        self.assertIsNotNone(result)
        self.assertRegex(result, r"\d{2}-\d{2}-\d{4}")

    @patch("file_processor.exifread.process_file", side_effect=Exception("read error"))
    @patch("builtins.open", new_callable=mock_open)
    @patch("file_processor.Path.stat", side_effect=OSError("no stat"))
    def test_returns_none_on_all_failures(self, _mock_stat, _mock_file, _mock_exif):
        result = get_creation_date(Path("bad.jpg"))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()