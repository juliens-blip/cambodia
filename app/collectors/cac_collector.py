"""Cashew Association of Cambodia (CAC) PDF collector."""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.utils.pdf_parser import PDFParser
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class CACCollector(BaseCollector):
    """Collector for CAC PDF reports and communiques."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        seed_paths: Optional[List[str]] = None,
        commodity: str = "cashew",
        max_pdfs: Optional[int] = None,
        max_pages: Optional[int] = None,
        timeout: float = 30.0
    ):
        super().__init__("CAC")
        self.base_url = (base_url or settings.cac_base_url).rstrip("/")
        self.seed_paths = seed_paths or self._split_paths(settings.cac_seed_paths)
        if not self.seed_paths:
            self.seed_paths = ["/"]
        self.commodity = commodity
        self.max_pdfs = max_pdfs if max_pdfs is not None else settings.cac_max_pdfs
        self.max_pages = max_pages if max_pages is not None else settings.cac_max_pages
        self.timeout = timeout
        self.parser = PDFParser()
        self.link_patterns = ["/report", "/news"]

    async def collect(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        seen_urls = set()
        seen_pages = set()
        page_queue = [self._normalize_url(path) for path in self.seed_paths]

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            while page_queue and len(seen_pages) < self.max_pages:
                page_url = page_queue.pop(0)
                if page_url in seen_pages:
                    continue
                seen_pages.add(page_url)
                html = await self._fetch_html(client, page_url)
                if not html:
                    continue

                pdf_links = self._extract_pdf_links(html, page_url)
                for pdf_url in pdf_links:
                    if pdf_url in seen_urls:
                        continue
                    if len(seen_urls) >= self.max_pdfs:
                        break
                    seen_urls.add(pdf_url)

                    content = await self._download_pdf(client, pdf_url)
                    if not content:
                        continue

                    text = self.parser.extract_text(content)
                    if not text:
                        logger.warning("CAC PDF has no text: %s", pdf_url)
                        continue

                    title = self._derive_title(pdf_url)
                    context_record = {
                        "document_type": "context",
                        "source": "CAC",
                        "commodity": self.commodity,
                        "title": title,
                        "text_content": text,
                        "url": pdf_url,
                        "scraped_at": datetime.utcnow().isoformat(),
                        "char_count": len(text),
                        "extraction_method": "ocr" if len(text) > 100 else "text"
                    }
                    records.append(context_record)

                    production_records = self.parser.extract_production_data(text, self.commodity, title)
                    for record in production_records:
                        record["source"] = "CAC"
                        record["commodity"] = self.commodity
                    records.extend(production_records)

                if len(seen_pages) < self.max_pages:
                    for link in self._extract_page_links(html, page_url):
                        if link in seen_pages or link in page_queue:
                            continue
                        page_queue.append(link)

        return records

    async def validate(self, data: Dict[str, Any]) -> bool:
        if data.get("document_type") == "context":
            required_fields = ["commodity", "source", "title", "text_content"]
            if not all(field in data for field in required_fields):
                return False
            return data["commodity"] in ["cashew", "rubber"]

        required_fields = ["commodity", "source", "year", "province"]
        if not all(field in data for field in required_fields):
            return False
        return data["commodity"] in ["cashew", "rubber"]

    async def _fetch_html(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            logger.warning("CAC page fetch failed (%s): %s", url, exc)
            return None

    async def _download_pdf(self, client: httpx.AsyncClient, url: str) -> Optional[bytes]:
        try:
            response = await client.get(url)
            response.raise_for_status()
            if "pdf" not in response.headers.get("content-type", "").lower():
                logger.warning("CAC URL is not PDF: %s", url)
            return response.content
        except Exception as exc:
            logger.warning("CAC PDF download failed (%s): %s", url, exc)
            return None

    def _extract_pdf_links(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if self._looks_like_pdf(href):
                links.append(urljoin(page_url, href))
        return list(dict.fromkeys(links))

    def _extract_page_links(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            full_url = urljoin(page_url, href)
            if self._is_candidate_page(full_url):
                links.append(full_url)
        return list(dict.fromkeys(links))

    def _normalize_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def _derive_title(self, pdf_url: str) -> str:
        parsed = urlparse(pdf_url)
        filename = os.path.basename(parsed.path)
        return filename or "cac-report"

    def _looks_like_pdf(self, href: str) -> bool:
        return ".pdf" in href.lower()

    def _is_candidate_page(self, url: str) -> bool:
        parsed = urlparse(url)
        if "cac-camcashew.org" not in parsed.netloc:
            return False
        if parsed.path.lower().endswith(".pdf"):
            return False
        for pattern in self.link_patterns:
            if pattern in parsed.path.lower():
                return True
        return False

    def _split_paths(self, raw_value: str) -> List[str]:
        if not raw_value:
            return []
        return [item.strip() for item in raw_value.split(",") if item.strip()]
