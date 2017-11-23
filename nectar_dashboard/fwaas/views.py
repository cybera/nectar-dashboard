from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import render

from horizon import messages

from swiftclient import client as swiftclient

from nectar_dashboard.fwaas import fwaas

import requests


def handle_panos_errors(func):
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status >= 400 and status < 500:
                messages.error(args[0], _('Invalid password or deactivation key'))
            else:
                messages.error(args[0], _('Unknown error with PAN-OS API'))
        except requests.exceptions.RequestException:
            messages.error(args[0], _('Unknown error with PAN-OS API'))
        return JsonResponse({})

    return _wrapper

class FwaasView(TemplateView):
    template_name = 'fwaas/index.html'

    def get(self, request, *args, **kwargs):
        try:
            backups = fwaas.get_backups(request)
        except swiftclient.ClientException:
            messages.error(request, _('List of backups could not be retrieved'))
            backups = []
        status = fwaas.get_status(request)
        addr = ""
        if status == fwaas.Status.RUNNING:
            launch_enabled = False
            backup_enabled = True
            upgradeable = fwaas.instance_upgradeable(request)
            addr = fwaas.get_ipv4_address(request)
        elif status == fwaas.Status.NOT_RUNNING:
            launch_enabled = True
            backup_enabled = False
            upgradeable = False
        else:
            launch_enabled = False
            backup_enabled= False
            upgradeable = False
        return render(request, self.template_name, {"backups": backups, "upgradeable": upgradeable, "launch_enabled": launch_enabled, "backup_enabled": backup_enabled, "status": status, "addr": addr})

def launch(request):
    if fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance already exists'))
    else:
        password = request.POST["password"]
        fwaas.launch_instance(request, password=password)
    return JsonResponse({})

@handle_panos_errors
def backup(request):
    if not fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance does not exist'))
    else:
        password = request.POST["password"]
        fwaas.create_backup(request, password)
    return JsonResponse({})

@handle_panos_errors
def recover(request):
    backup_id = request.POST["backup_id"]
    deact_key = request.POST["deact_key"]
    password = request.POST["password"]
    fwaas.recover_instance(request, backup_id, deact_key, password)
    return JsonResponse({})

@handle_panos_errors
def upgrade(request):
    if not fwaas.instance_exists(request):
        messages.error(request, _('Firewall instance does not exist'))
    else:
        deact_key = request.POST["deact_key"]
        password = request.POST["password"]
        fwaas.upgrade_instance(request, deact_key, password)
    return JsonResponse({})

def status(request):
    status = fwaas.get_status(request)
    upgradeable = False
    addr = ""
    if status == fwaas.Status.RUNNING:
        upgradeable = fwaas.instance_upgradeable(request)
        addr = fwaas.get_ipv4_address(request)
    return JsonResponse({"status": status, "upgradeable": upgradeable, "address": addr})

def destroy(request):
    deact_key = request.GET["deact_key"]
    password = request.GET["password"]
    fwaas.delicense_instance(request, deact_key, password)
    fwaas.destroy_instance(request)
    return JsonResponse({})
