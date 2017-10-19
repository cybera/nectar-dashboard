from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import render

from horizon import messages
from horizon import forms
from horizon import tables

from nectar_dashboard.fwaas import fwaas


class FwaasView(TemplateView):
    template_name = 'fwaas/index.html'

    def get(self, request, *args, **kwargs):
        backups = fwaas.get_backups(request)
        return render(request, self.template_name, {"backups": backups})

def launch(request):
    if fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance already exists'))
    else:
        fwaas.launch_instance(request)
    return JsonResponse({})

def backup(request):
    if not fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance does not exist'))
    else:
        fwaas.create_backup(request)
    return JsonResponse({})

def recover(request):
    backup_id = request.POST["backup_id"]
    deact_key = request.POST["deact_key"]
    fwaas.recover_instance(request, backup_id, deact_key)
    return JsonResponse({})

def upgrade(request):
    if not fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance does not exist'))
    else:
        deact_key = request.POST["deact_key"]
        fwaas.upgrade_instance(request, deact_key)
    return JsonResponse({})
