"""Unit tests for PDF Parser module."""
import pytest
from unittest.mock import Mock, patch
from app.utils.pdf_parser import PDFParser


@pytest.fixture
def sample_pdf_text():
    """Sample text extracted from PDF."""
    return """
    Cambodia Agricultural Production Report 2023

    Kampong Cham Province
    Cashew Production: 1500 tons
    Cultivation Area: 2000 hectares

    Battambang Province
    Rubber Production: 3500 tons
    Cultivation Area: 4000 ha
    """


@pytest.fixture
def sample_pdf_bytes():
    """Sample PDF bytes (minimal PDF structure)."""
    # Minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
187
%%EOF"""


class TestPDFParser:
    """Test PDFParser class."""

    def test_init_tesseract_available(self):
        """Test PDFParser initialization checks tesseract."""
        parser = PDFParser()
        assert hasattr(parser, 'tesseract_available')
        assert isinstance(parser.tesseract_available, bool)

    def test_extract_text_pypdf_success(self, sample_pdf_bytes):
        """Test text extraction from modern PDF."""
        parser = PDFParser()

        # Mock pypdf PdfReader
        with patch('app.utils.pdf_parser.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Test content from PDF"
            mock_reader.return_value.pages = [mock_page]

            text = parser._extract_text_pypdf(sample_pdf_bytes)

            assert text == "Test content from PDF"
            mock_reader.assert_called_once()

    def test_extract_text_pypdf_failure(self):
        """Test text extraction failure returns empty string."""
        parser = PDFParser()

        with patch('app.utils.pdf_parser.PdfReader', side_effect=Exception("Invalid PDF")):
            text = parser._extract_text_pypdf(b"invalid pdf data")

            assert text == ""

    def test_extract_text_with_fallback(self, sample_pdf_bytes):
        """Test extract_text with OCR fallback when text is empty."""
        parser = PDFParser()

        # Mock pypdf returns empty, OCR returns text
        with patch.object(parser, '_extract_text_pypdf', return_value=""):
            with patch.object(parser, '_extract_text_ocr', return_value="OCR extracted text"):
                parser.tesseract_available = True

                text = parser.extract_text(sample_pdf_bytes)

                assert text == "OCR extracted text"

    def test_extract_production_data_cashew(self, sample_pdf_text):
        """Test extraction of cashew production data from text."""
        parser = PDFParser()

        records = parser.extract_production_data(
            sample_pdf_text,
            commodity="cashew",
            filename="report_2023.pdf"
        )

        assert len(records) >= 1
        # Check first record structure
        record = records[0]
        assert record["commodity"] == "cashew"
        assert "province" in record
        assert "year" in record
        assert "production_tons" in record or "area_hectares" in record

    def test_extract_production_data_no_matches(self):
        """Test extraction with text containing no production data."""
        parser = PDFParser()

        records = parser.extract_production_data(
            "This PDF contains no production data.",
            commodity="cashew",
            filename="empty.pdf"
        )

        assert records == []

    def test_graceful_degradation_no_tesseract(self, sample_pdf_bytes):
        """Test fallback when tesseract not available."""
        parser = PDFParser()
        parser.tesseract_available = False

        # Mock pypdf returns empty text
        with patch.object(parser, '_extract_text_pypdf', return_value=""):
            text = parser.extract_text(sample_pdf_bytes)

            # Should return empty without crashing
            assert text == ""
