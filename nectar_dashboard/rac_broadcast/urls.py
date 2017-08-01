from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from nectar_dashboard.rac_broadcast import views


urlpatterns = patterns('nectar_dashboard.rac_broadcast.views',
    url(r'^$', views.RACBroadcastView.as_view(), name='index'),
    url(r'^index$', views.RACBroadcastView.as_view(), name='index'),
)
