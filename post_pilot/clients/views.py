from django.views.generic import TemplateView
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator


# @method_decorator(never_cache, name='dispatch')
class HomeView(TemplateView):
    template_name = 'clients/home.html'

   # def get_queryset(self):
    #    user = self.request.user
   #     qs = super().get_queryset()
    #    if user.is_authenticated and (user.is_staff or is_moderator(user)):
    #        return qs  # показать все
    #    return qs.filter(is_published=True)  # только опубликованные
