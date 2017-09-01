from django.conf import settings
from django.core.urlresolvers import reverse
from django.fwaas.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.http import JsonResponse

from horizon import exceptions
from horizon import forms
from horizon import tables

import .fwaas


class FwaasView(TemplateView):
    template_name = 'fwaas/index.html'

    def get(self, request, *args, **kwargs):
        pass

class BackupsView(TemplateView):
    template_name = 'fwaas/backups.html'

    def get(self, request, *args, **kwargs):
        fwaas.get_backups()

def launch(request):
    if fwaas.fw_instance_exists():
        exceptions.handle(request, _('Firewall instance already exists'))

    fwaas.launch_fw_instance()

def backup(request):
    if not fwaas.fw_instance_exists():
        exceptions.handle(request, _('Firewall instance does not exist'))

    fwaas.backup_fw_instance

def recover(request):
    backup_id = request.POST["backup_id"]
    recover_fw_instance(backup_id)

def upgrade(request):
    if not fwaas.fw_instance_exists():
        exceptions.handle(request, _('Firewall instance does not exist'))

    fwaas.upgrade_fw_instance
