"""PDF Parser module for extracting text and production data from PDF files."""
import io
import os
import re
import shutil
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class PDFParser:
    """
    PDF Parser for extracting text and production data.

    Supports two extraction methods:
    1. Text extraction (pypdf) - Fast, works for modern PDFs
    2. OCR (pdf2image + pytesseract) - Thorough, works for scans

    Automatically falls back to OCR if text extraction yields < 50 chars.
    """

    def __init__(self):
        """Initialize PDF parser and check tesseract availability."""
        self.tesseract_available = self._check_tesseract()
        if not self.tesseract_available:
            logger.info("Tesseract not available - OCR will be skipped")

    def _check_tesseract(self) -> bool:
        """
        Check if tesseract is available on the system.

        Returns:
            True if tesseract is available, False otherwise
        """
        try:
            # Try to find tesseract in PATH
            if shutil.which("tesseract"):
                return True

            # Try to import and check pytesseract config
            from pytesseract import pytesseract

            # Use settings instead of os.getenv()
            tesseract_cmd = settings.tesseract_cmd
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.tesseract_cmd = tesseract_cmd
                return True

            return False
        except Exception:
            return False

    def extract_text(self, data: bytes) -> str:
        """
        Extract text from PDF using hybrid approach.

        Tries text extraction first (fast), falls back to OCR (thorough).

        Args:
            data: PDF file content as bytes

        Returns:
            Extracted text or empty string if extraction failed
        """
        # Try text extraction first (fast)
        text = self._extract_text_pypdf(data)

        if text and len(text) > 50:
            logger.debug("PDF text extraction successful")
            return text

        # Fallback to OCR if text extraction yields insufficient text
        if self.tesseract_available:
            logger.debug("Text extraction insufficient, falling back to OCR")
            text = self._extract_text_ocr(data)
            if text:
                logger.debug("PDF OCR extraction successful")
                return text

        if not text:
            logger.warning("PDF text extraction and OCR both failed")

        return text

    def _extract_text_pypdf(self, data: bytes) -> str:
        """
        Extract text from PDF using pypdf library.

        Args:
            data: PDF file content as bytes

        Returns:
            Extracted text or empty string on failure
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))

            # Limit to first 5 pages for performance
            max_pages = min(5, len(reader.pages))
            extracted = []

            for i in range(max_pages):
                page_text = reader.pages[i].extract_text() or ""
                extracted.append(page_text)

            text = "\n".join(extracted).strip()
            return text

        except Exception as e:
            logger.debug(f"pypdf text extraction failed: {e}")
            return ""

    def _extract_text_ocr(self, data: bytes) -> str:
        """
        Extract text from PDF using OCR (pdf2image + pytesseract).

        Args:
            data: PDF file content as bytes

        Returns:
            Extracted text or empty string on failure
        """
        try:
            from pdf2image import convert_from_bytes
            from pytesseract import image_to_string, pytesseract

            # Configure tesseract using settings
            tesseract_cmd = settings.tesseract_cmd
            tessdata_prefix = settings.tessdata_prefix

            if tessdata_prefix:
                os.environ["TESSDATA_PREFIX"] = tessdata_prefix
            if tesseract_cmd:
                pytesseract.tesseract_cmd = tesseract_cmd

            # Configure poppler (for Windows)
            poppler_path = settings.poppler_path

            # Convert PDF to images (first 5 pages only)
            images = convert_from_bytes(
                data,
                dpi=300,
                first_page=1,
                last_page=5,
                poppler_path=poppler_path if poppler_path else None
            )

            # OCR each image (Khmer + English)
            ocr_text = []
            for image in images:
                text = image_to_string(image, lang="khm+eng", config="--psm 6")
                ocr_text.append(text)

            return "\n".join(ocr_text).strip()

        except Exception as e:
            logger.debug(f"PDF OCR failed: {e}")
            return ""

    def extract_production_data(
        self,
        text: str,
        commodity: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Extract production data from PDF text using pattern matching.

        Looks for patterns like:
        - Province: Kampong Cham, Production: 1000 tons, Area: 500 ha
        - Year: 2023, Province: Kratie, Tons: 2500

        Args:
            text: Extracted PDF text
            commodity: Commodity name (e.g., "cashew", "rubber")
            filename: Source filename (for metadata)

        Returns:
            List of production records
        """
        if not text:
            return []

        records = []

        # Extract year from text or filename
        year_match = re.search(r'20[0-9]{2}', text + filename)
        default_year = int(year_match.group(0)) if year_match else datetime.now().year

        # Cambodian provinces (English and Khmer romanization)
        provinces = [
            "Kampong Cham", "Kampong Thom", "Kratie", "Mondulkiri", "Ratanakiri",
            "Stung Treng", "Preah Vihear", "Kampong Speu", "Pursat", "Battambang",
            "Banteay Meanchey", "Oddar Meanchey", "Pailin", "Siem Reap", "Kampot",
            "Kep", "Koh Kong", "Preah Sihanouk", "Takeo", "Kandal", "Prey Veng",
            "Svay Rieng", "Tbong Khmum", "Phnom Penh"
        ]

        # Pattern 1: Province + production data in same paragraph
        for province in provinces:
            # Case-insensitive search for province
            province_pattern = re.compile(rf'\b{re.escape(province)}\b', re.IGNORECASE)

            if province_pattern.search(text):
                # Look for production numbers near province name (±200-500 chars context)
                context_start = max(0, text.lower().find(province.lower()) - 200)
                context_end = min(len(text), text.lower().find(province.lower()) + 500)
                context = text[context_start:context_end]

                # Extract production tons
                production_match = re.search(
                    r'(\d+[\d,]*\.?\d*)\s*(?:tons|tonnes|metric tons|MT)',
                    context,
                    re.IGNORECASE
                )
                production = float(production_match.group(1).replace(',', '')) if production_match else None

                # Extract area hectares
                area_match = re.search(
                    r'(\d+[\d,]*\.?\d*)\s*(?:ha|hectares|hectare|hec)',
                    context,
                    re.IGNORECASE
                )
                area = float(area_match.group(1).replace(',', '')) if area_match else None

                # Extract year if present in context
                year_match = re.search(r'20[0-9]{2}', context)
                year = int(year_match.group(0)) if year_match else default_year

                if production or area:
                    records.append({
                        "commodity": commodity,
                        "year": year,
                        "province": province,
                        "production_tons": production,
                        "area_hectares": area,
                        "metadata": {
                            "filename": filename,
                            "extracted_method": "pdf_pattern_matching",
                            "extraction_date": datetime.utcnow().isoformat()
                        }
                    })

        # Pattern 2: Tabular data (rows with province, year, production)
        # Example: "Kampong Cham 2023 1500 tons 800 ha"
        table_pattern = r'([A-Za-z\s]+)\s+(20[0-9]{2})\s+(\d+[\d,]*\.?\d*)\s*(?:tons|tonnes)?\s+(\d+[\d,]*\.?\d*)\s*(?:ha|hectares)?'
        table_matches = re.findall(table_pattern, text, re.IGNORECASE)

        for match in table_matches:
            province_candidate = match[0].strip()

            # Check if it matches a known province
            if any(prov.lower() in province_candidate.lower() for prov in provinces):
                year = int(match[1])
                production = float(match[2].replace(',', ''))
                area = float(match[3].replace(',', '')) if match[3] else None

                records.append({
                    "commodity": commodity,
                    "year": year,
                    "province": province_candidate,
                    "production_tons": production,
                    "area_hectares": area,
                    "metadata": {
                        "filename": filename,
                        "extracted_method": "pdf_table_pattern",
                        "extraction_date": datetime.utcnow().isoformat()
                    }
                })

        # Deduplicate records (province, year) unique
        unique_records = []
        seen = set()

        for record in records:
            key = (record["province"], record["year"])
            if key not in seen:
                seen.add(key)
                unique_records.append(record)

        if unique_records:
            logger.info(f"Extracted {len(unique_records)} production records from {filename}")
        else:
            logger.debug(f"No production records found in {filename}")

        return unique_records
