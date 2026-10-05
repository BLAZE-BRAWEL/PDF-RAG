from celery import Celery
from ..config import settings

celery_app = Celery(
    'background_job',
    broker = settings.celery_broker_url,
    backend = settings.celery_backend_url,
    include = ["app.workers.worker"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)