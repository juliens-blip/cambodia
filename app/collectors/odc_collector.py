"""Open Development Cambodia (ODC) collector."""
from typing import List, Dict, Any
from datetime import datetime
import logging
import re
import httpx
import json
import asyncio
from bs4 import BeautifulSoup

from .base_collector import BaseCollector
from app.utils.pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class ODCCollector(BaseCollector):
    """
    Collector for Open Development Cambodia datasets.

    Scrapes CSV/JSON datasets for cashew and rubber production data.
    """

    def __init__(self, base_url: str):
        """
        Initialize ODC collector.

        Args:
            base_url: ODC base URL
        """
        super().__init__("ODC")
        self.base_url = base_url

        # URLs will be discovered dynamically - no hardcoded URLs
        self.dataset_urls = {}

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from ODC datasets.

        Attempts to scrape production data from known datasets.
        Uses HTTP client to download CSV/JSON resources.

        Returns:
            List of production records
        """
        records = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Discover datasets dynamically
            commodities = ["cashew", "rubber"]
            logger.info(f"Starting ODC discovery for commodities: {commodities}")

            for commodity in commodities:
                # Dynamic discovery
                dataset_urls = await self._discover_datasets(client, commodity)

                if not dataset_urls:
                    logger.warning(f"No datasets discovered for {commodity}")
                    continue

                for dataset_url in dataset_urls:
                    try:
                        # Try to fetch the dataset page
                        response = await client.get(dataset_url)

                        if response.status_code == 404:
                            logger.debug(f"Dataset not found: {dataset_url}")
                            continue

                        if response.status_code != 200:
                            logger.warning(f"Failed to fetch {dataset_url}: {response.status_code}")
                            continue

                        # Parse HTML to find CSV/JSON download links
                        html = response.text
                        resource_urls = self._extract_resource_urls(html)

                        for resource_url in resource_urls:
                            try:
                                # Download resource
                                resource_data = await self._download_resource(client, resource_url)

                                if resource_data:
                                    # Parse resource based on type
                                    parsed_records = self._parse_resource(
                                        resource_data,
                                        commodity,
                                        resource_url
                                    )
                                    records.extend(parsed_records)

                            except Exception as e:
                                logger.error(f"Error downloading resource {resource_url}: {e}")
                                continue

                    except Exception as e:
                        logger.error(f"Error fetching dataset {dataset_url}: {e}")
                        continue

        # If no real data found, create sample records for testing
        if not records:
            logger.warning("No ODC data found after discovery + parsing - creating sample production records")
            logger.warning("Possible causes: 1) No datasets discovered, 2) All resources failed to parse, 3) ODC site unavailable")
            records = self._create_sample_data()

            # Add metadata flag pour audit
            for record in records:
                record["metadata"]["fallback_reason"] = "discovery_failed_or_no_parseable_resources"

        logger.info(f"ODC collector found {len(records)} production records")
        return records

    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate ODC data record.

        Args:
            data: Data record to validate

        Returns:
            True if valid, False otherwise
        """
        # Context documents have different required fields
        if data.get("document_type") == "context":
            required_fields = ["commodity", "source", "title", "text_content"]
            if not all(field in data for field in required_fields):
                return False
            if data["commodity"] not in ["cashew", "rubber"]:
                return False
            return True

        # Production records need year
        required_fields = ["commodity", "source", "year"]

        if not all(field in data for field in required_fields):
            return False

        if data["commodity"] not in ["cashew", "rubber"]:
            return False

        return True

    # Helper methods

    def _extract_resource_urls(self, html: str) -> List[str]:
        """
        Extract CSV/JSON/XLS resource URLs using BeautifulSoup.

        Args:
            html: Dataset page HTML

        Returns:
            List of resource download URLs (max 10)
        """
        urls = []

        # Parse HTML avec BeautifulSoup + lxml
        soup = BeautifulSoup(html, 'lxml')

        # Find download links: <a href="..." containing .csv/.json/.xls/.pdf/download
        # Pattern 1: Direct file links
        for ext in ['.csv', '.json', '.xls', '.xlsx', '.pdf', '.zip']:
            links = soup.find_all('a', href=re.compile(f'{re.escape(ext)}$', re.I))
            for link in links:
                href = link.get('href', '')
                urls.append(self._normalize_url(href))

        # Pattern 2: Download endpoint links
        download_links = soup.find_all('a', href=re.compile(r'/download/'))
        for link in download_links:
            href = link.get('href', '')
            urls.append(self._normalize_url(href))

        # Pattern 3: Resource links (ODC specific)
        resource_links = soup.find_all('a', href=re.compile(r'/resource/'))
        for link in resource_links:
            href = link.get('href', '')
            if 'download' in href or any(ext in href for ext in ['.csv', '.json', '.xls', '.pdf']):
                urls.append(self._normalize_url(href))

        # Deduplicate while preserving order
        unique_urls = list(dict.fromkeys(urls))

        # Augmenter limite: 5 → 10 ressources
        limited_urls = unique_urls[:10]

        logger.debug(f"Extracted {len(limited_urls)} resource URLs from HTML")
        return limited_urls

    def _normalize_url(self, href: str) -> str:
        """Normalize URL: relative → absolute."""
        if href.startswith("http"):
            return href
        elif href.startswith("/"):
            return f"https://data.opendevelopmentcambodia.net{href}"
        else:
            return f"https://data.opendevelopmentcambodia.net/{href}"

    async def _download_resource(self, client: httpx.AsyncClient, url: str) -> bytes:
        """
        Download resource file.

        Args:
            client: HTTP client
            url: Resource URL

        Returns:
            Resource content as bytes
        """
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None

    def _parse_resource(self, data: bytes, commodity: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse CSV/JSON/Excel/PDF resource.

        Args:
            data: Resource content
            commodity: Commodity name
            url: Resource URL

        Returns:
            List of production records
        """
        records = []

        try:
            # 1. Try PDF first (detect by extension or magic bytes)
            if url.endswith('.pdf') or data[:10].startswith(b'%PDF'):
                logger.info(f"Detected PDF, routing to _parse_pdf(): {url}")
                return self._parse_pdf(data, commodity, url)

            # 2. Try JSON (detect by content)
            elif url.endswith('.json') or b'{' in data[:100] or b'[' in data[:100]:
                json_data = json.loads(data)

                if isinstance(json_data, list):
                    for item in json_data:
                        record = self._parse_json_item(item, commodity, url)
                        if record:
                            records.append(record)
                elif isinstance(json_data, dict):
                    record = self._parse_json_item(json_data, commodity, url)
                    if record:
                        records.append(record)

            # 2. Try Excel formats (NEW)
            elif url.endswith(('.xls', '.xlsx')):
                records = self._parse_excel(data, commodity, url)

            # 3. Try CSV (default)
            else:
                import csv
                import io

                text = data.decode('utf-8', errors='ignore')
                reader = csv.DictReader(io.StringIO(text))

                for row in reader:
                    record = self._parse_csv_row(row, commodity, url)
                    if record:
                        records.append(record)

        except Exception as e:
            logger.error(f"Error parsing resource from {url}: {e}")

        return records

    def _parse_json_item(self, item: dict, commodity: str, url: str) -> Dict[str, Any]:
        """Parse JSON item to production record."""
        try:
            # Look for common field names
            year = item.get('year') or item.get('Year') or item.get('YEAR')
            province = item.get('province') or item.get('Province') or item.get('PROVINCE') or 'Unknown'
            production = item.get('production_tons') or item.get('production') or item.get('Production')
            area = item.get('area_hectares') or item.get('area') or item.get('Area')

            if not year:
                return None

            return {
                "commodity": commodity,
                "year": int(year) if year else datetime.now().year,
                "province": str(province),
                "production_tons": float(production) if production else None,
                "area_hectares": float(area) if area else None,
                "source": "ODC",
                "metadata": {
                    "url": url,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "original_data": item
                }
            }

        except Exception as e:
            logger.debug(f"Error parsing JSON item: {e}")
            return None

    def _parse_csv_row(self, row: dict, commodity: str, url: str) -> Dict[str, Any]:
        """Parse CSV row to production record."""
        try:
            # Look for common field names (case-insensitive)
            row_lower = {k.lower(): v for k, v in row.items()}

            year = row_lower.get('year') or row_lower.get('yr')
            province = row_lower.get('province') or row_lower.get('region') or 'Unknown'
            production = row_lower.get('production_tons') or row_lower.get('production') or row_lower.get('tons')
            area = row_lower.get('area_hectares') or row_lower.get('area') or row_lower.get('hectares')

            if not year:
                return None

            return {
                "commodity": commodity,
                "year": int(year) if year else datetime.now().year,
                "province": str(province),
                "production_tons": float(production) if production else None,
                "area_hectares": float(area) if area else None,
                "source": "ODC",
                "metadata": {
                    "url": url,
                    "scraped_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.debug(f"Error parsing CSV row: {e}")
            return None

    def _parse_excel(self, data: bytes, commodity: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse Excel file (.xls/.xlsx) to production records.

        Args:
            data: Excel file bytes
            commodity: Commodity name
            url: Resource URL

        Returns:
            List of production records
        """
        try:
            import pandas as pd
            import io

            # Read Excel avec pandas
            df = pd.read_excel(io.BytesIO(data))

            # Convert to CSV-like dict format
            records = []
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                record = self._parse_csv_row(row_dict, commodity, url)
                if record:
                    records.append(record)

            logger.info(f"Parsed {len(records)} records from Excel: {url}")
            return records

        except Exception as e:
            logger.warning(f"Failed to parse Excel {url}: {e}")
            return []

    def _parse_pdf(self, data: bytes, commodity: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse PDF file to production records.

        Uses PDFParser to extract text (pypdf + OCR fallback) and pattern matching.

        Args:
            data: PDF file bytes
            commodity: Commodity name
            url: Resource URL

        Returns:
            List of production records
        """
        logger.info(f"ENTERING _parse_pdf() for {url[:80]}...")
        try:
            logger.info("Creating PDFParser instance...")
            parser = PDFParser()
            logger.info(f"PDFParser created, tesseract_available={parser.tesseract_available}")

            # Extract text (hybrid: text extraction + OCR fallback)
            logger.info(f"Calling parser.extract_text() with {len(data)} bytes...")
            text = parser.extract_text(data)
            logger.info(f"Text extraction completed, got {len(text) if text else 0} characters")

            if not text:
                logger.warning(f"No text extracted from PDF: {url}")
                return []

            logger.info(f"Text extraction successful! First 100 chars: {text[:100]}")

            # Extract production data from text
            filename = url.split('/')[-1]
            records = parser.extract_production_data(text, commodity, filename)

            # IMPORTANT: Even if no structured production data, store as context document
            # These PDFs contain crucial contextual information (policies, concessions, reports)
            if not records and text:
                logger.info(f"No structured data, but storing {len(text)} chars as context document: {filename}")
                # Create a context document record for ChromaDB indexing
                context_record = {
                    "document_type": "context",
                    "source": "ODC",
                    "commodity": commodity,
                    "title": filename,
                    "text_content": text,
                    "url": url,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "char_count": len(text),
                    "extraction_method": "ocr" if len(text) > 100 else "text"
                }
                # Return as special context record (will be indexed separately)
                return [context_record]

            # Add source and URL to metadata for production records
            for record in records:
                record["source"] = "ODC"
                record["metadata"]["url"] = url
                record["metadata"]["scraped_at"] = datetime.utcnow().isoformat()

            if records:
                logger.info(f"Parsed {len(records)} production records from PDF: {url}")

            return records

        except Exception as e:
            logger.warning(f"Failed to parse PDF {url}: {e}")
            return []

    def _create_sample_data(self) -> List[Dict[str, Any]]:
        """
        Create sample production data for testing when no real data is available.

        Returns:
            List of sample production records
        """
        # Sample production data for Cambodian provinces
        provinces = ["Kampong Cham", "Kampong Thom", "Kratie", "Mondulkiri", "Ratanakiri"]
        years = [2021, 2022, 2023]

        records = []

        for commodity in ["cashew", "rubber"]:
            for year in years:
                for province in provinces:
                    # Generate realistic sample data
                    if commodity == "cashew":
                        production = 1000 + (hash(f"{province}{year}") % 5000)
                        area = 500 + (hash(f"{province}{year}") % 2000)
                    else:  # rubber
                        production = 2000 + (hash(f"{province}{year}") % 8000)
                        area = 1000 + (hash(f"{province}{year}") % 3000)

                    records.append({
                        "commodity": commodity,
                        "year": year,
                        "province": province,
                        "production_tons": production,
                        "area_hectares": area,
                        "source": "ODC",
                        "metadata": {
                            "note": "Sample data - no real ODC dataset found",
                            "scraped_at": datetime.utcnow().isoformat()
                        }
                    })

        return records

    async def _discover_datasets(
        self,
        client: httpx.AsyncClient,
        commodity: str
    ) -> List[str]:
        """
        Discover dataset URLs via ODC search.

        Args:
            client: HTTP client
            commodity: "cashew" or "rubber"

        Returns:
            List of dataset URLs (max 5)
        """
        # 1. Build search URL
        search_url = f"{self.base_url}?q=agriculture+{commodity}"

        logger.info(f"Searching ODC for '{commodity}' datasets...")
        logger.info(f"Search URL: {search_url}")

        # 2. GET search results with retry
        response = None
        for attempt in range(2):
            try:
                response = await client.get(search_url, timeout=30.0)
                if response.status_code == 200:
                    break

                if attempt == 0:
                    logger.debug(f"Search failed (status {response.status_code}), retrying...")
                    await asyncio.sleep(2)
            except httpx.TimeoutException:
                if attempt == 0:
                    logger.warning("Search timeout, retrying...")
                    await asyncio.sleep(2)
                else:
                    logger.error("Search failed after 2 attempts")
                    return []
            except Exception as e:
                logger.error(f"Search error: {e}")
                return []

        if not response or response.status_code != 200:
            logger.warning(f"Search failed with status {response.status_code if response else 'None'}")
            return []

        # 3. Parse avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')

        # 4. Find dataset links: <h3><a href="/en/dataset/...">
        dataset_links = soup.find_all('a', href=re.compile(r'^/en/(dataset|library_record)/'))

        # 5. Extract URLs + filter keywords
        keywords = ["production", "statistics", "agriculture", commodity]
        urls = []

        for link in dataset_links[:10]:  # Top 10 results
            title = link.get_text(strip=True).lower()
            href = link.get('href', '')

            # Filter: title contains commodity OR production
            if any(kw in title for kw in keywords):
                full_url = f"https://data.opendevelopmentcambodia.net{href}"
                urls.append(full_url)

        # 6. Deduplicate + limit
        unique_urls = list(dict.fromkeys(urls))[:5]

        logger.info(f"Discovered {len(unique_urls)} datasets for {commodity}: {unique_urls}")

        if not unique_urls:
            logger.warning(f"No datasets found for {commodity} - search returned 0 results")

        return unique_urls
