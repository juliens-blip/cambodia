"""
CSX Index Helper for Streamlit UI
Provides simple functions to save/load CSX index from Supabase with file fallback
"""

import os
import json
from typing import Optional
from datetime import datetime
from pathlib import Path

# Try to import Supabase (may not be available in all environments)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


# File-based fallback path (absolute)
CSX_CACHE_FILE = Path(__file__).resolve().parent.parent.parent / "logs" / "csx_index_cache.json"


def _get_supabase_client() -> Optional[Client]:
    """Get Supabase client if credentials are available"""
    if not SUPABASE_AVAILABLE:
        return None

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        print(f"[CSX_HELPER] Failed to create Supabase client: {e}", flush=True)
        return None


def save_csx_index(value: float, change_percent: Optional[float] = None, updated_at: Optional[str] = None) -> bool:
    """
    Save CSX index to Supabase (primary) and file (fallback)

    Args:
        value: CSX index value
        change_percent: Percentage change
        updated_at: Timestamp string (ISO format)

    Returns:
        True if saved successfully, False otherwise
    """
    if updated_at is None:
        updated_at = datetime.utcnow().isoformat()

    data = {
        "value": value,
        "change_percent": change_percent,
        "updated_at": updated_at
    }

    # Try Supabase first
    supabase = _get_supabase_client()
    if supabase:
        try:
            result = supabase.table("csx_index").insert(data).execute()
            if result.data:
                print(f"[CSX_HELPER] Saved to Supabase: {value}", flush=True)
                # Also save to file as backup
                _save_to_file(data)
                return True
        except Exception as e:
            print(f"[CSX_HELPER] Failed to save to Supabase: {e}", flush=True)

    # Fallback to file
    return _save_to_file(data)


def get_latest_csx_index() -> Optional[dict]:
    """
    Get latest CSX index from Supabase (primary) or file (fallback)

    Returns:
        dict with 'value', 'change_percent', 'updated_at' if found, None otherwise
    """
    # Try Supabase first
    supabase = _get_supabase_client()
    if supabase:
        try:
            result = (
                supabase.table("csx_index")
                .select("value, change_percent, updated_at")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data and len(result.data) > 0:
                print(f"[CSX_HELPER] Loaded from Supabase", flush=True)
                return result.data[0]
        except Exception as e:
            print(f"[CSX_HELPER] Failed to load from Supabase: {e}", flush=True)

    # Fallback to file
    return _load_from_file()


def _save_to_file(data: dict) -> bool:
    """Save CSX index to file"""
    try:
        CSX_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CSX_CACHE_FILE.write_text(json.dumps(data), encoding="utf-8")
        print(f"[CSX_HELPER] Saved to file: {CSX_CACHE_FILE}", flush=True)
        return True
    except Exception as e:
        print(f"[CSX_HELPER] Failed to save to file: {e}", flush=True)
        return False


def _load_from_file() -> Optional[dict]:
    """Load CSX index from file"""
    try:
        if not CSX_CACHE_FILE.exists():
            return None
        data = json.loads(CSX_CACHE_FILE.read_text(encoding="utf-8"))
        print(f"[CSX_HELPER] Loaded from file: {CSX_CACHE_FILE}", flush=True)
        return data
    except Exception as e:
        print(f"[CSX_HELPER] Failed to load from file: {e}", flush=True)
        return None
