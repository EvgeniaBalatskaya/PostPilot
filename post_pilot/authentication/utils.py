from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from .models import Mailing

def generate_email_confirmation_token(user):
    return default_token_generator.make_token(user)

def encode_uid(user_pk):
    return urlsafe_base64_encode(force_bytes(user_pk))

def decode_uid(uidb64):
    return force_str(urlsafe_base64_decode(uidb64))

def update_mailings_status():
    """
    Обновление статусов всех рассылок:
    - 'Создана' → 'Запущена', если наступило start_time
    - 'Запущена' → 'Завершена', если прошло end_time
    """
    now = timezone.now()
    mailings = Mailing.objects.all()
    for mailing in mailings:
        updated = False
        if mailing.status == 'Создана' and mailing.start_time and now >= mailing.start_time:
            mailing.status = 'Запущена'
            updated = True
        if mailing.status == 'Запущена' and mailing.end_time and now >= mailing.end_time:
            mailing.status = 'Завершена'
            updated = True
        if updated:
            mailing.save()


def send_mailing(mailing, send_email_func):
    """
    Отправка письма всем получателям рассылки с записью попыток.
    send_email_func(email, subject, body) — функция отправки письма.
    """
    for recipient in mailing.recipients.all():
        try:
            send_email_func(recipient.email, mailing.message.subject, mailing.message.body)
            status = 'Успешно'
            response = 'OK'
        except Exception as e:
            status = 'Не успешно'
            response = str(e)

        MailingAttempt.objects.create(
            mailing=mailing,
            status=status,
            server_response=response
        )
