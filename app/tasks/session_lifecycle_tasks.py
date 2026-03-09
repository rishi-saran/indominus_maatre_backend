# /app/tasks/session_lifecycle_tasks.py
from datetime import datetime, timedelta, timezone
from app.core.celery_app import celery_app
from app.core.supabase import supabase
from app.services.stream_service import StreamService

# The frontend appends the datetime with a naive offset that gets mapped identically into Supabase.
# To match this bug/behavior properly in scheduled tasks, we use IST again.
IST = timezone(timedelta(hours=5, minutes=30))

@celery_app.task(bind=True)
def enable_backstage_task(self):
    now = datetime.now(tz=IST)

    window_start = now + timedelta(minutes=4)
    # Give a tiny buffer in case it skips a minute
    window_end = now + timedelta(minutes=6)

    # Note that timezone strings returned from Supabase look like `2026-03-06T05:14:00+00:00`
    response = (
        supabase
        .table("sessions")
        .select("id, stream_id")
        .eq("status", "approved")
        .eq("backstage_enabled", False)
        # We need to strictly format it to the ISO 8601 string Supabase expects
        .gte("start_time", window_start.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"))
        .lte("start_time", window_end.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"))
        .execute()
    )

    for session in response.data or []:
        if session["stream_id"]:
            StreamService.enable_backstage(session["stream_id"])

        supabase.table("sessions").update(
            {"backstage_enabled": True}
        ).eq("id", session["id"]).execute()


@celery_app.task(bind=True)
def start_session_task(self):
    now = datetime.now(tz=IST)

    # We want to catch instances where the start time is strictly 
    # less than or equal to current time + small buffer (so they start).
    response = (
        supabase
        .table("sessions")
        .select("id, stream_id")
        # Backstage sessions are still technically "approved".
        .eq("status", "approved") 
        .eq("live_started", False)
        .lte("start_time", now.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"))
        .execute()
    )

    for session in response.data or []:
        if session["stream_id"]:
            StreamService.start_call(session["stream_id"])

        supabase.table("sessions").update(
            {
                "status": "live",
                "live_started": True,
                "backstage_enabled": False  # Backstage warm-up window is over once session is live
            }
        ).eq("id", session["id"]).execute()


@celery_app.task(bind=True)
def end_session_task(self):
    now = datetime.now(tz=IST)

    response = (
        supabase
        .table("sessions")
        .select("id, stream_id")
        .eq("status", "live")
        .lte("end_time", now.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"))
        .execute()
    )

    for session in response.data or []:
        if session["stream_id"]:
            StreamService.end_call(session["stream_id"])

        supabase.table("sessions").update(
            {"status": "ended"}
        ).eq("id", session["id"]).execute()