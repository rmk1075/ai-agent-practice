import pdfplumber
from docx import Document


class FileTooLargeError(Exception):
    pass


class UnsupportedFileTypeError(Exception):
    pass


class FileParseError(Exception):
    pass


class FileParser:
    MAX_FILE_SIZE = 10 * 1024 * 1024
    SUPPORTED_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def parse(self, file) -> str:
        if file.content_type not in self.SUPPORTED_TYPES:
            raise UnsupportedFileTypeError(
                "Unsupported file type. Only PDF and DOCX are allowed."
            )
        if file.size > self.MAX_FILE_SIZE:
            raise FileTooLargeError("File size exceeds limit of 10MB.")
        try:
            if file.content_type == "application/pdf":
                return self._parse_pdf(file)
            return self._parse_docx(file)
        except MemoryError:
            raise
        except Exception as e:
            raise FileParseError("Failed to parse file.") from e

    def _parse_pdf(self, file) -> str:
        with pdfplumber.open(file) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()

    def _parse_docx(self, file) -> str:
        doc = Document(file)
        return "\n".join(para.text for para in doc.paragraphs if para.text).strip()
