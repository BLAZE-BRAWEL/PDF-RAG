from celery import Celery
from ..config import settings

celery_app = Celery(
    'background_job',
    broker = settings.celery_broker_url,
    backend = settings.celery_backend_url
)