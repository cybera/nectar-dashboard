from django.conf.urls import patterns
from django.conf.urls import url

from .views import RACQuotaChangeView


urlpatterns = patterns('',
    url(r'^$', RACQuotaChangeView.as_view(), name='index'),
)
