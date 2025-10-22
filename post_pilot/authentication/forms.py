from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import Recipient
from .models import Message, Mailing


class AuthForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "password1", "password2")

        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ['email', 'full_name', 'comment']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'message': forms.Select(attrs={'class': 'form-control'}),
            'recipients': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }