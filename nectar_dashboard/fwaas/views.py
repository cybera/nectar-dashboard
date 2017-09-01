from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.http import JsonResponse

from horizon import exceptions
from horizon import forms
from horizon import tables

import .utils


class FwaasView(TemplateView):
    template_name = 'fwaas/index.html'

    def get(self, request, *args, **kwargs):
        pass

class BackupsView(TemplateView):
    template_name = 'fwaas/backups.html'

    def get(self, request, *args, **kwargs):
        pass

def launch(request):
    if utils.fw_instance_exists():
        exceptions.handle(request, _('Firewall instance already exists'))

    utils.launch_fw_instance()

def backup(request):
    if not utils.fw_instance_exists():
        exceptions.handle(request, _('Firewall does not exist'))

    utils.backup_fw_instance

def recover(request):
    backup_id = request.POST["backup_id"]
    recover_fw_instance(backup_id)

def upgrade(request):
    if not utils.fw_instance_exists():
        exceptions.handle(request, _('Firewall does not exist'))

    utils.upgrade_fw_instance
