from celery import Celery
from celery.signals import worker_ready, beat_init
import logging
from celery.schedules import crontab
from src.config import config

logger = logging.getLogger(__name__)

app = Celery(
    'codeforces_parser',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=['src.celery.tasks'],
    broker_connection_retry_on_startup=True
)

# Базовая конфигурация
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    enable_utc=True,
    timezone='UTC',
    task_track_started=True,
    task_time_limit=3600,  # 1 час
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    task_default_priority=0,
    task_compression='gzip',
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    task_remote_control_enabled=True,
    task_send_sent_event=True,
    task_always_eager=False,
    task_eager_propagates=True,
    task_annotations={
        'src.parser.tasks.parse_codeforces': {
            'rate_limit': '10/m',
            'max_retries': 3,
            'retry_backoff': True,
            'retry_backoff_max': 600,
            'retry_jitter': True,
        }
    }
)

# Настройка очередей
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'parsing': {
        'exchange': 'parsing',
        'routing_key': 'parsing',
        'queue_arguments': {'x-max-priority': 10},
    }
}

# Настройка маршрутизации задач
app.conf.task_routes = {
    'src.parser.tasks.parse_codeforces': {'queue': 'parsing'}
}

# Настройка периодических задач
app.conf.beat_schedule = {
    'parse-codeforces': {
        'task': 'src.parser.tasks.parse_codeforces',
        'schedule': crontab(minute=0, hour='*'),  # Каждый час
    },
}

# Настройка повторных попыток
app.conf.task_acks_late = True  # Подтверждение выполнения после успешного завершения
app.conf.task_reject_on_worker_lost = True  # Перезапуск задачи при потере воркера


def init_celery(**kwargs):
    """
    Инициализация Celery при старте воркера
    """
    sender = kwargs.get('sender')
    if sender and sender.app.amqp.default_queue.name == 'parsing':
        logger.info("Starting initial parsing task")
        from src.celery.tasks import parse_codeforces
        parse_codeforces.delay()
    else:
        logger.info("Worker does not handle parsing queue, skipping initial parse")


# Логирование при старте beat
@beat_init.connect
def on_beat_init(**kwargs):
    """Инициализация при запуске Celery beat"""
    logger.info("Celery beat started")


# Обработчик сигнала готовности воркера
@worker_ready.connect
def at_start(**kwargs):
    """
    Запускает парсинг при старте воркера, если он обрабатывает очередь parsing
    """
    init_celery(**kwargs)
