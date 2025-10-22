import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('post_pilot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'auto-update-mailings-every-minute': {
        'task': 'yourapp.tasks.auto_update_mailings',
        'schedule': 60.0,  # каждые 60 секунд
    },
}