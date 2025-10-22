from .utils import generate_email_confirmation_token, encode_uid
from django import forms
from django.contrib.auth import get_user_model
from django.views import View
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from .utils import decode_uid
from django.urls import reverse_lazy
from .forms import RecipientForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.views.generic import CreateView, DetailView
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_control
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from .models import Mailing, Message, Recipient
from .forms import MailingForm, MessageForm
from .utils import update_mailings_status, send_mailing

import logging
logger = logging.getLogger(__name__)
User = get_user_model()

class AuthForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")


class AuthCreateView(CreateView):
    model = User
    form_class = AuthForm
    template_name = 'authentication/auth_create.html'
    success_url = reverse_lazy('authentication:auth_login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        current_site = get_current_site(self.request)
        mail_subject = 'Подтвердите ваш email'
        uid = encode_uid(user.pk)
        token = generate_email_confirmation_token(user)
        message = render_to_string('authentication/email_confirmation.html', {
            'user': user,
            'domain': current_site.domain,
            'uidb64': uid,  # ✅ исправлено имя параметра
            'token': token,
        })
        send_mail(mail_subject, message, None, [user.email])

        messages.success(self.request, "Проверьте почту и подтвердите email для активации аккаунта.")
        return redirect(self.success_url)


class ActivateEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = decode_uid(uidb64)
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.is_email_confirmed = True
            user.save()
            return HttpResponse('Спасибо! Email подтвержден. Теперь вы можете войти.')
        else:
            return HttpResponse('Ссылка недействительна или просрочена.')

class CustomLoginView(LoginView):
    template_name = 'authentication/auth_login.html'

    def get_success_url(self):
        return reverse('authentication:auth_detail', kwargs={'pk': self.request.user.pk})


class AuthDetailView(DetailView):
    model = User
    template_name = 'authentication/auth_detail.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mailings = Mailing.objects.filter(user=self.object)
        context['total_mailings'] = mailings.count()
        context['active_mailings'] = mailings.filter(status='Запущена').count()
        context['recipients_count'] = Recipient.objects.filter(user=self.object).count()
        return context

# Главная страница управления рассылками
@login_required
def mailing_management(request):
    update_mailings_status()

    if request.user.is_superuser:
        all_messages = Message.objects.all()
        mailings = Mailing.objects.all()
    else:
        all_messages = Message.objects.filter(user=request.user)
        mailings = Mailing.objects.filter(user=request.user)

    context = {
        'all_messages': all_messages,
        'mailings': mailings,
        'message_form': MessageForm(),
        'mailing_form': MailingForm(),
    }
    return render(request, 'authentication/auth_mailings.html', context)


@login_required
def create_message(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        if subject and body:
            Message.objects.create(user=request.user, subject=subject, body=body)
            messages.success(request, "Сообщение успешно создано!")
        else:
            messages.error(request, "Заполните все поля.")
    return redirect('authentication:auth_mailings')


@login_required
def create_mailing(request):
    if request.method == 'POST':
        form = MailingForm(request.POST)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.user = request.user
            mailing.save()
            form.save_m2m()
            messages.success(request, "Рассылка создана!")
        else:
            messages.error(request, "Ошибка при создании рассылки.")
    return redirect('authentication:auth_mailings')


@login_required
def start_mailing(request, mailing_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})

    mailing = get_object_or_404(Mailing, id=mailing_id)
    now = timezone.now()

    # Если время окончания уже прошло — статус Завершена
    if mailing.end_time and now >= mailing.end_time:
        if mailing.status != 'Завершена':
            mailing.status = 'Завершена'
            mailing.save()
        return JsonResponse({'success': True, 'status': mailing.status})

    # Переключение статуса только если рассылка не завершена
    if mailing.status == 'Создана':
        mailing.status = 'Запущена'
        mailing.save()
    elif mailing.status == 'Запущена':
        mailing.status = 'Создана'
        mailing.save()

    return JsonResponse({'success': True, 'status': mailing.status})



@login_required
def mailings_status_api(request):
    now = timezone.now()
    mailings = Mailing.objects.all()
    for mailing in mailings:
        if mailing.status == 'Создана' and mailing.start_time and now >= mailing.start_time:
            mailing.status = 'Запущена'
            mailing.save()
        elif mailing.status == 'Запущена' and mailing.end_time and now >= mailing.end_time:
            mailing.status = 'Завершена'
            mailing.save()
    data = [
        {"id": m.id, "status": m.status}
        for m in mailings
    ]
    return JsonResponse({"mailings": data})


@login_required
def delete_mailing(request, mailing_id):
    if request.method == 'POST':
        mailing = get_object_or_404(Mailing, id=mailing_id)
        mailing.delete()
        messages.success(request, "Рассылка удалена!")
    return redirect('authentication:auth_mailings')



@login_required
def delete_message(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(Message, id=message_id)
        msg.delete()
        messages.success(request, "Сообщение удалено!")
    return redirect('authentication:auth_mailings')


@login_required
def edit_message(request, message_id):
    msg = get_object_or_404(Message, id=message_id)
    if request.method == 'POST':
        msg.subject = request.POST.get('subject')
        msg.body = request.POST.get('body')
        msg.save()
        messages.success(request, "Сообщение обновлено!")
    return redirect('authentication:auth_mailings')


@login_required
def edit_mailing(request, mailing_id):
    mailing = get_object_or_404(Mailing, id=mailing_id)
    if request.method == 'POST':
        mailing.start_time = request.POST.get('start_time')
        mailing.end_time = request.POST.get('end_time')
        mailing.message_id = request.POST.get('message')
        mailing.recipients.set(request.POST.getlist('recipients'))
        mailing.save()
        messages.success(request, "Рассылка обновлена!")
    return redirect('authentication:auth_mailings')

#auth_member
@login_required
def auth_member(request):
    form = RecipientForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            form = RecipientForm(request.POST)
            if form.is_valid():
                recipient = form.save(commit=False)
                recipient.user = request.user
                recipient.save()
                return redirect('authentication:auth_member')
        elif action == "edit":
            recipient_id = request.POST.get("recipient_id")
            recipient = get_object_or_404(Recipient, pk=recipient_id, user=request.user)
            form = RecipientForm(request.POST, instance=recipient)
            if form.is_valid():
                form.save()
                return redirect('authentication:auth_member')
        elif action == "delete":
            recipient_id = request.POST.get("recipient_id")
            recipient = get_object_or_404(Recipient, pk=recipient_id, user=request.user)
            recipient.delete()
            return redirect('authentication:auth_member')

    recipients = Recipient.objects.filter(user=request.user).order_by("id")
    recipients_count = recipients.count()

    context = {
        "form": form,
        "recipients": recipients,
        "recipients_count": recipients_count,
    }
    return render(request, "authentication/auth_member.html", context)


#auth_stats
@login_required
def auth_stats(request):
    if request.user.is_superuser:
        mailings = Mailing.objects.all()
        messages_qs = Message.objects.all()
    else:
        mailings = Mailing.objects.filter(user=request.user)
        messages_qs = Message.objects.filter(user=request.user)

    total_mailings = mailings.count()
    successful_mailings = mailings.filter(status='Завершена').count()
    failed_mailings = mailings.filter(status='Создана').count()

    total_messages = messages_qs.count()
    sent_messages = sum(m.recipients.count() for m in mailings.filter(status='Завершена'))

    context = {
        'total_mailings': total_mailings,
        'successful_mailings': successful_mailings,
        'failed_mailings': failed_mailings,
        'total_messages': total_messages,
        'sent_messages': sent_messages,
    }

    return render(request, "authentication/auth_stats.html", context)


@login_required
def messages_api(request):
    messages = Message.objects.filter(user=request.user).values('id', 'subject', 'body')
    return JsonResponse({'messages': list(messages)})

@login_required
def mailings_api(request):
    mailings = Mailing.objects.filter(user=request.user).values(
        'id', 'status', 'start_time', 'end_time', 'message_id', 'message__subject'
    )
    return JsonResponse({'mailings': list(mailings)})

@login_required
def members_data_api(request):
    recipients = Recipient.objects.filter(user=request.user).order_by("id")
    data = {
        "recipients": [
            {"id": r.id, "email": r.email, "full_name": r.full_name, "comment": r.comment}
            for r in recipients
        ]
    }
    return JsonResponse(data)



@login_required
def stats_data_api(request):
    if request.user.is_superuser:
        mailings = Mailing.objects.all()
        messages_qs = Message.objects.all()
    else:
        mailings = Mailing.objects.filter(user=request.user)
        messages_qs = Message.objects.filter(user=request.user)

    data = {
        "total_mailings": mailings.count(),
        "successful_mailings": mailings.filter(status='Завершена').count(),
        "failed_mailings": mailings.filter(status='Создана').count(),
        "total_messages": messages_qs.count(),
        "sent_messages": sum(m.recipients.count() for m in mailings.filter(status='Завершена')),
    }
    return JsonResponse(data)

