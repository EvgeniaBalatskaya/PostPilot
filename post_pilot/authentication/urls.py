from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import (
    CustomLoginView, AuthCreateView, ActivateEmailView,
    AuthDetailView, auth_member, auth_stats,
    mailing_management, create_mailing,
    start_mailing, delete_mailing, delete_message, create_message, edit_message, edit_mailing, messages_api,
    members_data_api, stats_data_api, mailings_api, mailings_status_api
)

app_name = 'authentication'
urlpatterns = [
     path("login/", CustomLoginView.as_view(), name="auth_login"),
     path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
     path('create/', AuthCreateView.as_view(), name='auth_create'),
     path('activate/<uidb64>/<token>/', ActivateEmailView.as_view(), name='activate'),
     path('<int:pk>/', AuthDetailView.as_view(), name='auth_detail'),

#password reset
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='authentication/password_reset.html',
             email_template_name='authentication/password_reset_email.html',
             success_url='/authentication/password_reset/?sent=true'
         ),
         name='password_reset'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='authentication/password_reset_confirm.html',
             success_url='/authentication/login/'
         ),
         name='password_reset_confirm'),


#auth_member
     path('member/', auth_member, name='auth_member'),

#auth_mailing
     path('mailings/', mailing_management, name='auth_mailings'),
     path('mailings/create-mailing/', create_mailing, name='create_mailing'),
     path('mailings/create-message/', create_message, name='create_message'),
     path('mailings/start-mailing/<int:mailing_id>/', start_mailing, name='start_mailing'),
     path('mailings/delete-mailing/<int:mailing_id>/', delete_mailing, name='delete_mailing'),
     path('mailings/delete-message/<int:message_id>/', delete_message, name='delete_message'),
     path('mailings/edit-message/<int:message_id>/', edit_message, name='edit_message'),
     path('edit_mailing/<int:mailing_id>/', edit_mailing, name='edit_mailing'),

#auth_stats
     path('stats/', auth_stats, name='auth_stats'),

#api
    path('api/messages_api/', messages_api, name='messages_api'),
    path('api/mailings_api/', mailings_api, name='mailings_api'),
    path('api/members_data/', members_data_api, name='members_data_api'),
    path('api/stats_data/', stats_data_api, name='stats_data_api'),
    path('mailings/status/', mailings_status_api, name='mailings_status_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)