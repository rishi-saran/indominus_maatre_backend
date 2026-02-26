from datetime import datetime, timedelta, timezone
from app.core.celery_app import celery_app
from app.core.supabase import supabase

IST = timezone(timedelta(hours=5, minutes=30))


@celery_app.task(bind=True)
def enable_backstage_task(self):
    now = datetime.now(tz=IST)

    window_start = now + timedelta(minutes=4)
    window_end = now + timedelta(minutes=5)

    response = (
        supabase
        .table("sessions")
        .select("id")
        .eq("status", "approved")
        .eq("backstage_enabled", False)
        .gte("start_time", window_start.isoformat())
        .lte("start_time", window_end.isoformat())
        .execute()
    )

    for session in response.data or []:
        # todo: Stream API call will go here later

        supabase.table("sessions").update(
            {"backstage_enabled": True}
        ).eq("id", session["id"]).execute()

@celery_app.task(bind=True)
def start_session_task(self):
    now = datetime.now(tz=IST)

    response = (
        supabase
        .table("sessions")
        .select("id")
        .eq("status", "approved")
        .eq("live_started", False)
        .lte("start_time", now.isoformat())
        .execute()
    )

    for session in response.data or []:
        # todo: Stream API call will go here later

        supabase.table("sessions").update(
            {
                "status": "live",
                "live_started": True
            }
        ).eq("id", session["id"]).execute()

@celery_app.task(bind=True)
def end_session_task(self):
    now = datetime.now(tz=IST)

    response = (
        supabase
        .table("sessions")
        .select("id")
        .eq("status", "live")
        .lte("end_time", now.isoformat())
        .execute()
    )

    for session in response.data or []:
        # todo: Stream API call will go here later

        supabase.table("sessions").update(
            {"status": "ended"}
        ).eq("id", session["id"]).execute()