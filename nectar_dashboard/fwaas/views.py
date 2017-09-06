from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.http import JsonResponse

from horizon import exceptions
from horizon import forms
from horizon import tables

from nectar_dashboard.fwaas import fwaas


class FwaasView(TemplateView):
    template_name = 'fwaas/index.html'

class BackupsView(TemplateView):
    template_name = 'fwaas/backups.html'

    def get(self, request, *args, **kwargs):
        fwaas.get_backups()

def launch(request):
    if fwaas.instance_exists():
        exceptions.handle(request, _('Firewall instance already exists'))

    fwaas.launch_instance()
    return JsonResponse({})

def backup(request):
    if not fwaas.instance_exists():
        exceptions.handle(request, _('Firewall instance does not exist'))

    fwaas.create_backup()
    return JsonResponse({})

def recover(request):
    backup_id = request.POST["backup_id"]
    fwaas.recover_instance(backup_id)
    return JsonResponse({})

def upgrade(request):
    if not fwaas.instance_exists():
        exceptions.handle(request, _('Firewall instance does not exist'))

    fwaas.upgrade_instance
    return JsonResponse({})
