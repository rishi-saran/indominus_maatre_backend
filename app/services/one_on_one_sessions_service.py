# /app/services/one_on_one_sessions_service.py

from datetime import datetime 
from uuid import UUID
from app.core.supabase import supabase

def assign_priest(
    start_time: datetime,
    end_time: datetime
) -> UUID:

    day_of_week = start_time.weekday() #* 0 -> monday, 6 -> sunday

    query = supabase.rpc(
        "assign_next_priest",
        {
            "p_day_of_week": day_of_week,
            "p_start_time": start_time.isoformat(),
            "p_end_time": end_time.isoformat(),
        }
    ).execute()

    if not query.data:
        raise ValueError("No priest available")

    return UUID(query.data[0]["priest_id"])