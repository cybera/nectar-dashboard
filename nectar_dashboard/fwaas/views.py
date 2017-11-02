from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import render

from horizon import messages

from swiftclient import client as swiftclient

from nectar_dashboard.fwaas import fwaas


class FwaasView(TemplateView):
    template_name = 'fwaas/index.html'

    def get(self, request, *args, **kwargs):
        try:
            backups = fwaas.get_backups(request)
        except swiftclient.ClientException:
            messages.error(request, _('List of backups could not be retrieved'))
            backups = []
        upgradeable = fwaas.instance_upgradeable(request)
        running = fwaas.instance_exists(request)
        return render(request, self.template_name, {"backups": backups, "upgradeable": upgradeable, "running": running})

def launch(request):
    if fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance already exists'))
    else:
        password = request.POST["password"]
        fwaas.launch_instance(request, password=password)
    return JsonResponse({})

def backup(request):
    if not fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance does not exist'))
    else:
        password = request.POST["password"]
        fwaas.create_backup(request, password)
    return JsonResponse({})

def recover(request):
    backup_id = request.POST["backup_id"]
    #deact_key = request.POST["deact_key"]
    deact_key = "46c8754f95907bd01c75f702636f3be2f2bf70aaccc5ed619973529180c3dd09"
    password = request.POST["password"]
    fwaas.recover_instance(request, backup_id, deact_key, password)
    return JsonResponse({})

def upgrade(request):
    if not fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance does not exist'))
    else:
        deact_key = request.POST["deact_key"]
        password = request.POST["password"]
        fwaas.upgrade_instance(request, deact_key, password)
    return JsonResponse({})
