from celery import shared_task
from .models import Mailing

@shared_task
def auto_update_mailings():
    now = timezone.now()
    mailings = Mailing.objects.exclude(status='Завершена')
    for mailing in mailings:
        if mailing.status == 'Создана' and mailing.start_time and now >= mailing.start_time:
            mailing.status = 'Запущена'
            mailing.save()
        elif mailing.status == 'Запущена' and mailing.end_time and now >= mailing.end_time:
            mailing.status = 'Завершена'
            mailing.save()
