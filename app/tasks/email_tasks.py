from app.core.celery_app import celery_app
from app.core.supabase import supabase
from app.services.email_service import EmailService
from app.email_templates.session_confirmation import (
    build_session_confirmation_email
)
from app.email_templates.session_reminder import (
    build_session_reminder_email
)
from datetime import datetime, timedelta, timezone


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def send_confirmation_email_task(self, session_id: str):
    session = (
        supabase
        .table("sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
        .data
    )
    user = (
        supabase
        .table("users")
        .select("email")
        .eq("id", session["customer_id"])
        .single()
        .execute()
        .data
    )

    if not session or session["confirmation_email_sent"]:
        return

    join_url = f"https://localhost:3000/join/{session_id}"
    subject, body = build_session_confirmation_email(join_url)


    try:
        EmailService.send_html_email(
            # to_email = user["email"]
            to_email="sanjay.savitha05@gmail.com",
            subject=subject,
            html_body=body
        )
    except Exception as e:
        print("EMAIL SEND FAILED:", e)
        raise

    supabase.table("sessions").update(
        {"confirmation_email_sent": True}
    ).eq("id", session_id).execute()


IST = timezone(timedelta(hours=5, minutes=30))

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def send_reminder_email_task(self):
    now = datetime.now(tz=IST)

    window_start = now + timedelta(minutes=4)
    window_end = now + timedelta(minutes=6)

    response = (
        supabase
        .table("sessions")
        .select("*")
        .eq("status", "approved")
        .eq("reminder_email_sent", False)
        .gte("start_time", window_start.isoformat())
        .lte("start_time", window_end.isoformat())
        .execute()
    )

    for session in response.data or []:
        user = (
            supabase
            .table("users")
            .select("email")
            .eq("id", session["customer_id"])
            .single()
            .execute()
            .data
        )

        join_url = f"https://localhost:3000/join/{session['id']}"
        subject, body = build_session_reminder_email(join_url)

        EmailService.send_html_email(
            # to_email=user["email"]
            to_email="sanjay.savitha05@gmail.com",
            subject=subject,
            html_body=body
        )

        supabase.table("sessions").update(
            {"reminder_email_sent": True}
        ).eq("id", session["id"]).execute()