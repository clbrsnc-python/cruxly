import os
import sys
from datetime import datetime
import pytz
from supabase import create_client

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.processor import run_ingestion_cycle  # noqa: E402

IST = pytz.timezone("Asia/Kolkata")


def determine_edition_slot() -> str:
    """Selects 'morning' for 06:00 AM IST window or 'evening' for 06:00 PM IST window."""
    explicit_slot = (os.getenv("EDITION_SLOT") or "").strip().lower()
    if explicit_slot in ("morning", "evening", "live"):
        return explicit_slot
    current_hour_ist = datetime.now(IST).hour
    return "morning" if current_hour_ist < 14 else "evening"


def main() -> None:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip() or None
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
    since_date = (os.getenv("SINCE_DATE") or "").strip() or None
    exhaustive_flag = (os.getenv("EXHAUSTIVE_MODE") or "").strip().lower() in ("1", "true", "yes")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables.")

    supabase = create_client(supabase_url, supabase_key)
    slot = determine_edition_slot()
    print(
        f"[{datetime.now(IST).isoformat()}] Starting scheduled Cruxly ingestion "
        f"(slot='{slot}', since_date='{since_date}', exhaustive={exhaustive_flag})..."
    )

    result = run_ingestion_cycle(
        supabase=supabase,
        gemini_api_key=gemini_api_key,
        groq_api_key=groq_api_key,
        edition_slot=slot,
        since_date=since_date,
        exhaustive=exhaustive_flag,
    )
    print(result["message"])


if __name__ == "__main__":
    main()
