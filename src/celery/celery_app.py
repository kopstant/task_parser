from celery import Celery
from src.config import config
from celery.schedules import crontab
from celery.signals import worker_ready, beat_init
import logging

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
    timezone='UTC'
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
    }
}

# Настройка маршрутизации задач
app.conf.task_routes = {
    'src.celery.tasks.parse_codeforces': {'queue': 'parsing'}
}

# Настройка периодических задач
app.conf.beat_schedule = {
    'parse-codeforces-hourly': {
        'task': 'src.celery.tasks.parse_codeforces',
        'schedule': 3600,  # Каждый час
        'options': {
            'queue': 'parsing',
            'expires': 3500,  # Задача истекает через час
        }
    }
}

# Настройка повторных попыток
app.conf.task_acks_late = True  # Подтверждение выполнения после успешного завершения
app.conf.task_reject_on_worker_lost = True  # Перезапуск задачи при потере воркера


def init_celery(sender):
    """
    Инициализация Celery при старте воркера
    """
    if sender.app.amqp.default_queue.name == 'parsing':
        logger.info("Starting initial parsing task")
        from src.celery.tasks import parse_codeforces
        parse_codeforces.delay()
    else:
        logger.info("Worker does not handle parsing queue, skipping initial parse")


# Логирование при старте beat
@beat_init.connect
def on_beat_init(sender, **kwargs):
    logger.info("Celery beat started. Scheduled tasks:")
    for task_name, task_config in sender.app.conf.beat_schedule.items():
        logger.info(f"Task: {task_name}")
        logger.info(f"  - Schedule: {task_config['schedule']}")
        logger.info(f"  - Queue: {task_config.get('options', {}).get('queue', 'default')}")


# Обработчик сигнала готовности воркера
@worker_ready.connect
def at_start(sender, **kwargs):
    """
    Запускает парсинг при старте воркера, если он обрабатывает очередь parsing
    """
    init_celery(sender)
