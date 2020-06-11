import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.usage import quotas

from horizon import forms
from horizon import messages

LOG = logging.getLogger(__name__)

SUPPORTED_RESOURCES = ('floating_ips',)


class RACQuotaChangeForm(forms.SelfHandlingForm):
    floating_ips = forms.IntegerField(
        initial=0,
        max_value=1,
        label=_('Floating IPs'),
        required=False)

    reason = forms.CharField(
        label=_('Reason for the change'),
        widget=forms.widgets.Textarea(),
        required=True)

    class Meta:
        name = _('Quota Change')

    def handle(self, request, data):
        current_quota = quotas.tenant_quota_usages(request)
        changes = {}
        for resource in SUPPORTED_RESOURCES:
            current = current_quota[resource]['quota']
            requested = data[resource]

            if current != requested and requested != 0:
                changes[resource] = {}
                changes[resource]['current'] = current
                changes[resource]['requested'] = requested

        if len(changes) > 0:
            email_body = "%s has requested a quota change:\n\n" % (request.user.username)
            for resource, v in changes.items():
                email_body += "%s: from %s to %s\n" % (resource, v['current'], v['requested'])
            email_body += "\n\n"
            email_body += "Reason: %s" % (data['reason'])

            email_destination = getattr(settings, 'RAC_EMAIL_DESTINATION')

            send_mail(
                'Quota change request from %s' % (request.user.username),
                email_body,
                email_destination,
                [email_destination],
            )

        messages.success(request, _('Your request has been submitted.'))
        return True
