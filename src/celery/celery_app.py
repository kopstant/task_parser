from __future__ import absolute_import
from celery import Celery
from celery.schedules import crontab
from src.config import config

app = Celery(
    'codeforces_parser',
    imports=['src.celery.tasks'],
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=['src.celery.tasks'],
    task_routes={
        'parse_codeforces_problems': {'queue': 'parsing'}
    }
)

app.conf.timezone = 'Europe/Moscow'

app.autodiscover_tasks(['src.celery.tasks'])

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'parsing': {
            'exchange': 'parsing',
            'routing_key': 'parsing',
        }
    }
)

app.conf.beat_schedule = {
    'parse-codeforces-hourly': {
        'task': 'src.celery.tasks.parse_codeforces_problems',
        'schedule': crontab(minute=0),  # Каждый час в :00 минут
        'options': {'queue': 'parsing'}
    },
}
app.conf.beat_schedule_filename = '/var/celery/celerybeat-schedule'
