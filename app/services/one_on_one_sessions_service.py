# /app/services/one_on_one_sessions_service.py

import datetime 
from uuid import UUID
from app.core.supabase import supabase

def assign_priest(
    start_time: datetime.datetime, 
    end_time :datetime.datetime
) -> UUID:
    # Return the UUID of the assigned priest

    return None