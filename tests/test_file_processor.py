import unittest
from pathlib import Path

from file_processor import get_file_type


class TestGetFileType(unittest.TestCase):
    def test_jpg_returns_image(self):
        self.assertEqual(get_file_type(Path("photo.jpg")), "image")

    def test_jpeg_uppercase_returns_image(self):
        self.assertEqual(get_file_type(Path("photo.JPEG")), "image")

    def test_png_returns_image(self):
        self.assertEqual(get_file_type(Path("image.png")), "image")

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


if __name__ == "__main__":
    unittest.main()
