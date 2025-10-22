from django.urls import path
from .views import HomeView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
 #  path('member/', views.clients, name='member'),  # страница "Клиенты"
 #  path('mailings/', views.mailings, name='mailings'),  # страница "Рассылки"
 #  path('stats/', views.stats, name='stats'),  # страница "Статистика"
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
