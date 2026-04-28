from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from conversation.file_parser import (
    FileParseError,
    FileParser,
    FileTooLargeError,
    UnsupportedFileTypeError,
)


class FileParserTest(TestCase):
    def _make_file(self, name, content, content_type, size=None):
        f = SimpleUploadedFile(name, content, content_type=content_type)
        if size is not None:
            f.size = size
        return f

    def test_parse_raises_file_too_large(self):
        f = self._make_file("big.pdf", b"x", "application/pdf", size=11 * 1024 * 1024)
        with self.assertRaises(FileTooLargeError):
            FileParser().parse(f)

    def test_parse_raises_unsupported_file_type(self):
        f = self._make_file("doc.txt", b"hello", "text/plain")
        with self.assertRaises(UnsupportedFileTypeError):
            FileParser().parse(f)

    @patch("conversation.file_parser.pdfplumber")
    def test_parse_pdf_returns_extracted_text(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "page text"
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value = mock_pdf

        f = self._make_file("test.pdf", b"%PDF-1.4", "application/pdf")
        result = FileParser().parse(f)
        self.assertEqual(result, "page text")

    @patch("conversation.file_parser.pdfplumber")
    def test_parse_pdf_handles_none_page_text(self, mock_pdfplumber):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = None
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "actual text"
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.open.return_value = mock_pdf

        f = self._make_file("test.pdf", b"%PDF-1.4", "application/pdf")
        result = FileParser().parse(f)
        self.assertEqual(result, "actual text")

    @patch("conversation.file_parser.Document")
    def test_parse_docx_returns_extracted_text(self, mock_document_cls):
        para1 = MagicMock()
        para1.text = "First paragraph"
        para2 = MagicMock()
        para2.text = "Second paragraph"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para1, para2]
        mock_document_cls.return_value = mock_doc

        f = self._make_file(
            "test.docx",
            b"fake",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        result = FileParser().parse(f)
        self.assertEqual(result, "First paragraph\nSecond paragraph")

    @patch("conversation.file_parser.pdfplumber")
    def test_parse_raises_file_parse_error_on_exception(self, mock_pdfplumber):
        mock_pdfplumber.open.side_effect = Exception("corrupted")
        f = self._make_file("bad.pdf", b"not a pdf", "application/pdf")
        with self.assertRaises(FileParseError):
            FileParser().parse(f)

    @patch("conversation.file_parser.Document")
    def test_parse_docx_skips_empty_paragraphs(self, mock_document_cls):
        para1 = MagicMock()
        para1.text = "First paragraph"
        empty_para = MagicMock()
        empty_para.text = ""
        para2 = MagicMock()
        para2.text = "Second paragraph"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para1, empty_para, para2]
        mock_document_cls.return_value = mock_doc

        f = self._make_file(
            "test.docx",
            b"fake",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        result = FileParser().parse(f)
        self.assertEqual(result, "First paragraph\nSecond paragraph")

    @patch("conversation.file_parser.Document")
    def test_parse_docx_raises_file_parse_error_on_exception(self, mock_document_cls):
        mock_document_cls.side_effect = Exception("corrupted docx")
        f = self._make_file(
            "bad.docx",
            b"corrupt",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        with self.assertRaises(FileParseError):
            FileParser().parse(f)

    def test_parse_raises_unsupported_type_before_size_check(self):
        f = self._make_file(
            "script.exe", b"MZ", "application/octet-stream", size=11 * 1024 * 1024
        )
        with self.assertRaises(UnsupportedFileTypeError):
            FileParser().parse(f)
