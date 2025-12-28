"""Google Drive collector for PDFs and KML files."""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import io
import json
import re
import os

from app.config import settings

from .base_collector import BaseCollector
from app.utils.pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class GDriveCollector(BaseCollector):
    """
    Collector for Google Drive PDF and KML documents.

    Handles OCR for Khmer documents using pytesseract.
    """

    def __init__(self, api_key: str, folder_ids: Optional[Dict[str, str]] = None):
        """
        Initialize Google Drive collector.

        Args:
            api_key: Google Drive API key
            folder_ids: Dict mapping commodity names to Google Drive folder IDs
                       e.g., {"cashew": "folder_id_1", "rubber": "folder_id_2"}
        """
        super().__init__("GDrive")
        self.api_key = api_key
        self.folder_ids = folder_ids or {}

        # Google Drive API endpoints
        self.base_url = "https://www.googleapis.com/drive/v3"

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect PDF/KML files from Google Drive folders.

        Returns:
            List of document metadata records
        """
        records = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for commodity, folder_id in self.folder_ids.items():
                try:
                    # List files in folder
                    files = await self._list_files(client, folder_id)

                    for file in files:
                        if file.get("mimeType") == "application/vnd.google-apps.folder":
                            continue

                        file_type = self._get_file_type(file["name"])

                        if file_type in ["pdf", "kml"]:
                            try:
                                # Download file
                                content = await self._download_file(client, file["id"])

                                # Process based on type
                                if file_type == "pdf":
                                    text = await self._extract_text_from_pdf(content)
                                    geolocation = None

                                    # Try to extract production data from PDF (or store as context)
                                    production_data = self._extract_production_from_text(
                                        text,
                                        commodity,
                                        file["name"],
                                        file["id"]  # Pass file_id for URL construction
                                    )

                                    if production_data:
                                        # Add production records OR context documents
                                        records.extend(production_data)

                                elif file_type == "kml":
                                    geolocation = await self._extract_kml_coordinates(content)
                                    text = f"KML file with {len(geolocation)} locations"

                                    # Try to extract production data from KML
                                    production_data = self._extract_production_from_kml(content, commodity, geolocation)

                                    if production_data:
                                        # Add production records
                                        records.extend(production_data)

                                else:
                                    geolocation = None
                                    text = ""

                                # Also add document record for ChromaDB
                                record = {
                                    "commodity": commodity,
                                    "type": "document",
                                    "file_name": file["name"],
                                    "file_type": file_type,
                                    "file_id": file["id"],
                                    "content": text[:5000],  # Truncate for storage
                                    "source": "GDrive",
                                    "metadata": {
                                        "file_size": file.get("size"),
                                        "created_time": file.get("createdTime"),
                                        "modified_time": file.get("modifiedTime"),
                                        "mime_type": file.get("mimeType"),
                                        "geolocation": geolocation if file_type == "kml" else None,
                                        "language": self._detect_language(text) if text else "unknown"
                                    }
                                }
                                records.append(record)
                            except Exception as exc:
                                logger.error("Error processing file %s: %s", file.get("name"), exc)
                                continue

                except Exception as e:
                    logger.error(f"Error collecting from folder {folder_id}: {e}")
                    continue

        return records

    async def _list_files(self, client: httpx.AsyncClient, folder_id: str) -> List[Dict[str, Any]]:
        """
        List files in a Google Drive folder.

        Args:
            client: HTTP client
            folder_id: Google Drive folder ID

        Returns:
            List of file metadata
        """
        url = f"{self.base_url}/files"
        files = []
        page_token = None

        while True:
            params = {
                "q": f"'{folder_id}' in parents",
                "key": self.api_key,
                "fields": "nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime)",
                "pageSize": 1000,
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true"
            }

            if page_token:
                params["pageToken"] = page_token

            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text[:500]
                logger.error("Google Drive list error (%s): %s", exc.response.status_code, detail)
                raise

            data = response.json()
            files.extend(data.get("files", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return files

    async def _download_file(self, client: httpx.AsyncClient, file_id: str) -> bytes:
        """
        Download file content from Google Drive.

        Args:
            client: HTTP client
            file_id: Google Drive file ID

        Returns:
            File content as bytes
        """
        url = f"{self.base_url}/files/{file_id}"
        params = {
            "alt": "media",
            "key": self.api_key,
            "supportsAllDrives": "true"
        }
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if content_type.startswith("text/html"):
                raise httpx.HTTPStatusError(
                    "Unexpected HTML response",
                    request=response.request,
                    response=response
                )

            return response.content
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            logger.error("Google Drive download error (%s): %s", exc.response.status_code, detail)
            return await self._download_file_public(client, file_id)

    async def _download_file_public(self, client: httpx.AsyncClient, file_id: str) -> bytes:
        url = "https://drive.google.com/uc"
        params = {"export": "download", "id": file_id}

        response = await client.get(url, params=params, follow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("text/html"):
            token = self._extract_confirm_token(response.text)
            if token:
                params["confirm"] = token
                response = await client.get(url, params=params, follow_redirects=True)
                response.raise_for_status()

        return response.content

    def _extract_confirm_token(self, html: str) -> Optional[str]:
        match = re.search(r"confirm=([0-9A-Za-z_]+)", html)
        if match:
            return match.group(1)
        return None

    async def _extract_text_from_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF using shared PDFParser (text extraction + OCR fallback).

        Args:
            content: PDF file content

        Returns:
            Extracted text
        """
        parser = PDFParser()
        return parser.extract_text(content)

    async def _extract_kml_coordinates(self, content: bytes) -> List[Dict[str, float]]:
        """
        Extract coordinates from KML file.

        Args:
            content: KML file content

        Returns:
            List of {lat, lon} coordinates
        """
        try:
            import xml.etree.ElementTree as ET

            # Parse KML
            root = ET.fromstring(content.decode("utf-8"))

            # KML namespace
            ns = {"kml": "http://www.opengis.net/kml/2.2"}

            coordinates = []

            # Extract placemarks
            for placemark in root.findall(".//kml:Placemark", ns):
                point = placemark.find(".//kml:Point/kml:coordinates", ns)
                if point is not None and point.text:
                    # KML format: lon,lat,altitude
                    coords = point.text.strip().split(",")
                    if len(coords) >= 2:
                        coordinates.append({
                            "lat": float(coords[1]),
                            "lon": float(coords[0])
                        })

            return coordinates

        except Exception as e:
            logger.error(f"Error parsing KML: {e}")
            return []

    def _get_file_type(self, filename: str) -> str:
        """Get file extension."""
        return filename.split(".")[-1].lower() if "." in filename else ""

    def _detect_language(self, text: str) -> str:
        """
        Detect if text contains Khmer characters.

        Args:
            text: Text to analyze

        Returns:
            'khmer', 'english', or 'mixed'
        """
        # Khmer Unicode range: 0x1780-0x17FF
        khmer_chars = sum(1 for char in text if '\u1780' <= char <= '\u17FF')
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)

        if khmer_chars > english_chars:
            return "khmer"
        elif english_chars > khmer_chars:
            return "english"
        else:
            return "mixed"

    def _extract_production_from_text(self, text: str, commodity: str, filename: str, file_id: str = None) -> List[Dict[str, Any]]:
        """
        Extract production data from PDF text using shared PDFParser.

        IMPORTANT: Even if no structured production data is found, returns
        the document as a context record. These PDFs contain crucial contextual
        information (policies, reports, market analyses) essential for final analysis.

        Args:
            text: Extracted PDF text
            commodity: Commodity name
            filename: Source filename
            file_id: Google Drive file ID (optional, for URL construction)

        Returns:
            List of production records OR context document records
        """
        if not text:
            return []

        parser = PDFParser()
        records = parser.extract_production_data(text, commodity, filename)

        # If structured data found, update source and return
        if records:
            for record in records:
                record["source"] = "GDrive"
            logger.info(f"Extracted {len(records)} production records from GDrive PDF: {filename}")
            return records

        # IMPORTANT: No structured data, but store as context document
        # These documents provide crucial contextual information
        logger.info(f"No structured data in GDrive PDF, but storing {len(text)} chars as context document: {filename}")

        # Construct Google Drive URL if file_id provided
        url = f"https://drive.google.com/file/d/{file_id}/view" if file_id else None

        context_record = {
            "document_type": "context",
            "source": "GDrive",
            "commodity": commodity,
            "title": filename,
            "text_content": text,
            "url": url,
            "scraped_at": datetime.utcnow().isoformat(),
            "char_count": len(text),
            "extraction_method": "ocr" if len(text) > 100 else "text"
        }

        return [context_record]

    def _extract_production_from_kml(self, content: bytes, commodity: str, coordinates: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Extract production data from KML file with geographic data.

        KML files may contain placemarks with production information.

        Args:
            content: KML file content
            commodity: Commodity name
            coordinates: Extracted coordinates

        Returns:
            List of production records
        """
        if not coordinates:
            return []

        records = []

        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(content.decode("utf-8"))
            ns = {"kml": "http://www.opengis.net/kml/2.2"}

            # Extract placemarks with extended data
            for placemark in root.findall(".//kml:Placemark", ns):
                name_elem = placemark.find(".//kml:name", ns)
                desc_elem = placemark.find(".//kml:description", ns)

                if name_elem is None:
                    continue

                name = name_elem.text or ""
                description = desc_elem.text if desc_elem is not None else ""

                # Try to extract province from name or description
                province = self._extract_province_from_text(name + " " + description)

                if not province:
                    continue

                # Extract year
                year_match = re.search(r'20[0-9]{2}', name + description)
                year = int(year_match.group(0)) if year_match else datetime.now().year

                # Extract production data from description
                production_match = re.search(r'(\d+[\d,]*\.?\d*)\s*(?:tons|tonnes|MT)', description, re.IGNORECASE)
                production = float(production_match.group(1).replace(',', '')) if production_match else None

                area_match = re.search(r'(\d+[\d,]*\.?\d*)\s*(?:ha|hectares)', description, re.IGNORECASE)
                area = float(area_match.group(1).replace(',', '')) if area_match else None

                # Get coordinates for this placemark
                point = placemark.find(".//kml:Point/kml:coordinates", ns)
                geolocation = None

                if point is not None and point.text:
                    coords = point.text.strip().split(",")
                    if len(coords) >= 2:
                        geolocation = {
                            "lat": float(coords[1]),
                            "lon": float(coords[0])
                        }

                if production or area:
                    records.append({
                        "commodity": commodity,
                        "year": year,
                        "province": province,
                        "production_tons": production,
                        "area_hectares": area,
                        "geolocation": geolocation,
                        "source": "GDrive",
                        "metadata": {
                            "extracted_method": "kml_parsing",
                            "placemark_name": name,
                            "extraction_date": datetime.utcnow().isoformat()
                        }
                    })

        except Exception as e:
            logger.error(f"Error extracting production from KML: {e}")

        return records

    def _extract_province_from_text(self, text: str) -> Optional[str]:
        """
        Extract province name from text.

        Args:
            text: Text to search

        Returns:
            Province name or None
        """
        provinces = [
            "Kampong Cham", "Kampong Thom", "Kratie", "Mondulkiri", "Ratanakiri",
            "Stung Treng", "Preah Vihear", "Kampong Speu", "Pursat", "Battambang",
            "Banteay Meanchey", "Oddar Meanchey", "Pailin", "Siem Reap", "Kampot",
            "Kep", "Koh Kong", "Preah Sihanouk", "Takeo", "Kandal", "Prey Veng",
            "Svay Rieng", "Tbong Khmum", "Phnom Penh"
        ]

        text_lower = text.lower()

        for province in provinces:
            if province.lower() in text_lower:
                return province

        return None

    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate Google Drive document record.

        Args:
            data: Data record to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["commodity", "source"]

        if not all(field in data for field in required_fields):
            return False

        if data["commodity"] not in ["cashew", "rubber"]:
            return False

        # Context documents (PDFs without structured data)
        if data.get("document_type") == "context":
            if "title" not in data or "text_content" not in data:
                return False
            return True

        # ChromaDB document records
        if data.get("type") == "document":
            if "file_name" not in data or "file_type" not in data:
                return False
            if data["file_type"] not in ["pdf", "kml"]:
                return False

        # Production records need year and province
        elif "year" in data:
            if "province" not in data:
                return False

        return True
