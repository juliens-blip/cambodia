"""
CSX Index Service
Handles persistence of Cambodia Stock Exchange index values in Supabase
"""

from typing import Optional
from datetime import datetime
from supabase import Client
from app.models.csx_index import CSXIndexCreate, CSXIndexResponse, CSXIndexLatest


class CSXIndexService:
    """Service for managing CSX index values in Supabase"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = "csx_index"

    async def save_csx_index(self, value: float, change_percent: Optional[float] = None) -> Optional[CSXIndexResponse]:
        """
        Save a new CSX index value to Supabase

        Args:
            value: CSX index value
            change_percent: Percentage change from previous day

        Returns:
            CSXIndexResponse if successful, None otherwise
        """
        try:
            data = {
                "value": value,
                "change_percent": change_percent,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table(self.table).insert(data).execute()

            if result.data and len(result.data) > 0:
                return CSXIndexResponse(**result.data[0])

            return None

        except Exception as e:
            print(f"[CSX_INDEX_SERVICE] Error saving CSX index: {e}", flush=True)
            return None

    async def get_latest_csx_index(self) -> Optional[CSXIndexLatest]:
        """
        Retrieve the most recent CSX index value from Supabase

        Returns:
            CSXIndexLatest if found, None otherwise
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("value, change_percent, updated_at")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data and len(result.data) > 0:
                data = result.data[0]
                return CSXIndexLatest(
                    value=data["value"],
                    change_percent=data.get("change_percent"),
                    updated_at=data["updated_at"]
                )

            return None

        except Exception as e:
            print(f"[CSX_INDEX_SERVICE] Error fetching latest CSX index: {e}", flush=True)
            return None

    def save_csx_index_sync(self, value: float, change_percent: Optional[float] = None) -> Optional[dict]:
        """
        Synchronous version of save_csx_index for use in Streamlit

        Args:
            value: CSX index value
            change_percent: Percentage change from previous day

        Returns:
            dict with saved data if successful, None otherwise
        """
        try:
            data = {
                "value": value,
                "change_percent": change_percent,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table(self.table).insert(data).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            print(f"[CSX_INDEX_SERVICE] Error saving CSX index (sync): {e}", flush=True)
            return None

    def get_latest_csx_index_sync(self) -> Optional[dict]:
        """
        Synchronous version of get_latest_csx_index for use in Streamlit

        Returns:
            dict with latest CSX index data if found, None otherwise
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("value, change_percent, updated_at")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            print(f"[CSX_INDEX_SERVICE] Error fetching latest CSX index (sync): {e}", flush=True)
            return None


# Global instance (initialized with supabase client)
_csx_index_service: Optional[CSXIndexService] = None


def get_csx_index_service(supabase: Client) -> CSXIndexService:
    """Get or create CSX index service instance"""
    global _csx_index_service
    if _csx_index_service is None:
        _csx_index_service = CSXIndexService(supabase)
    return _csx_index_service
