from django.db import models

class Newsletter(models.Model):
    STATUS_CHOICES = [
        ('CREATED', 'Создана'),
        ('LAUNCHED', 'Запущена'),
        ('FINISHED', 'Завершена'),
    ]

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='CREATED')
    message = models.ForeignKey('messages_app.Message', on_delete=models.CASCADE)
    clients = models.ManyToManyField('clients.Client')

    def __str__(self):
        return f"Рассылка #{self.pk}"

class NewsletterAttempt(models.Model):
    STATUS_CHOICES = [
        ('SUCCESS', 'Успешно'),
        ('FAILED', 'Не успешно'),
    ]
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE, related_name='attempts')
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    server_response = models.TextField()

    def __str__(self):
        return f"{self.newsletter} — {self.status} — {self.attempt_time}"
