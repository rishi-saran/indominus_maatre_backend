from app.core.celery_app import celery_app # noqa
from app.tasks import debug_tasks  # noqa
from app.tasks import session_lifecycle_tasks  # noqa
from app.tasks import email_tasks  # noqa


#! Note: remove "noqa" (i.e No Quality Assurance) might throw lint errors