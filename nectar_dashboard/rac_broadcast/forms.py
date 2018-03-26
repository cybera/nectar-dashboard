import logging

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

from nectar_dashboard import helpers

from . import utils

LOG = logging.getLogger(__name__)

MESSAGE_TYPES = (('general', 'General',), ('alert', 'Alert',))

class RACBroadcastForm(forms.SelfHandlingForm):
    message = forms.CharField(max_length=750, label=_("Broadcast Message"), required=False)
    message_type = forms.ChoiceField(widget=forms.RadioSelect, choices=MESSAGE_TYPES, label=_("Message Type"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(RACBroadcastForm, self).__init__(request, *args, **kwargs)
        project_id = request.user.tenant_id
        admin_project_id = utils.get_admin_project_id(request)
        if project_id == admin_project_id:
            project_id = "admin"
        message = helpers.get_message(project_id)
        self.fields['message'].initial = message[0]
        self.fields['message_type'].initial = message[1]
        if message[0] == "":
            self.fields['message_type'].initial = ""

    def handle(self, request, data):
        project_id = request.user.tenant_id
        admin_project_id = utils.get_admin_project_id(request)
        if project_id == admin_project_id:
            project_id = "admin"
        helpers.set_message(project_id, data['message'], data['message_type'])

        messages.success(request, _('Broadcast message set'))
        return True
