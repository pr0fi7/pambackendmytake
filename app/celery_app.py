from celery import Celery
from app.config import settings

celery_app = Celery(
    "harmix_pam",
    broker=f"{settings.REDIS_URL}/0",
    backend=f"{settings.REDIS_URL}/1",
)


celery_app.autodiscover_tasks(["app.worker"])


celery_app.conf.update(
    beat_scheduler="app.celery_db_scheduler.DatabaseScheduler",
)
