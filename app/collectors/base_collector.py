"""Base collector abstract class for data sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, source_name: str):
        """
        Initialize collector.

        Args:
            source_name: Name of the data source (e.g., 'MEF', 'WITS', 'ODC', 'GDrive')
        """
        self.source_name = source_name
        self.last_fetch: Optional[datetime] = None
        self.status: str = "initialized"
        self.error_log: List[Dict[str, Any]] = []

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from the source.

        Returns:
            List of data records (dicts)

        Raises:
            Exception: If collection fails
        """
        pass

    @abstractmethod
    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate a single data record.

        Args:
            data: Data record to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    async def run(self) -> List[Dict[str, Any]]:
        """
        Run the collector with error handling.

        Returns:
            List of validated data records
        """
        try:
            logger.info(f"Starting collection from {self.source_name}")
            self.status = "running"

            raw_data = await self.collect()
            logger.info(f"Collected {len(raw_data)} raw records from {self.source_name}")

            # Validate data
            validated_data = []
            for record in raw_data:
                if await self.validate(record):
                    validated_data.append(record)
                else:
                    logger.warning(f"Invalid record from {self.source_name}: {record}")

            self.last_fetch = datetime.utcnow()
            self.status = "success"
            logger.info(f"Validated {len(validated_data)}/{len(raw_data)} records from {self.source_name}")

            return validated_data

        except Exception as e:
            self.status = "error"
            error_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "type": type(e).__name__
            }
            self.error_log.append(error_record)
            logger.error(f"Collection failed from {self.source_name}: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Get collector status.

        Returns:
            Status dict with last_fetch, status, and error_log
        """
        return {
            "source_name": self.source_name,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
            "status": self.status,
            "error_count": len(self.error_log),
            "latest_error": self.error_log[-1] if self.error_log else None
        }
