from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "maathre",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "debug-every-minute": {
        "task": "app.tasks.debug_tasks.debug_task",
        "schedule": 60.0,
        "args": ("beat running",),
    }
}

celery_app.conf.beat_schedule.update({
    "enable-backstage-every-minute": {
        "task": "app.tasks.session_lifecycle_tasks.enable_backstage_task",
        "schedule": 60.0,
    },
    "start-session-every-minute": {
        "task": "app.tasks.session_lifecycle_tasks.start_session_task",
        "schedule": 60.0,
    },
    "end-session-every-minute": {
        "task": "app.tasks.session_lifecycle_tasks.end_session_task",
        "schedule": 60.0,
    },
})

celery_app.conf.beat_schedule.update({
    "send-reminder-email-every-minute": {
        "task": "app.tasks.email_tasks.send_reminder_email_task",
        "schedule": 60.0,
    },
})