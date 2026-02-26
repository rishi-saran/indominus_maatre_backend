from app.core.celery_app import celery_app
import time

@celery_app.task(bind=True)
def debug_task(self, message: str):
    print(f"[CELERY TASK START] {message}")
    time.sleep(2)
    print(f"[CELERY TASK END] {message}")
    return {"status": "ok", "message": message}