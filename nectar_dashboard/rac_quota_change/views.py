from horizon import forms

from openstack_dashboard.usage import quotas

from .forms import RACQuotaChangeForm

import logging
LOG = logging.getLogger(__name__)

from netaddr import *

class RACQuotaChangeView(forms.ModalFormView):
    form_class = RACQuotaChangeForm
    template_name = 'rac-quota-change/index.html'

    def get_context_data(self, **kwargs):
        context = super(RACQuotaChangeView, self).get_context_data(**kwargs)
        context['current_quota'] = quotas.tenant_quota_usages(self.request)
        context['remote_addr'] = IPAddress(self.request.META.get('HTTP_X_FORWARDED_FOR')).version
        return context

    def get_success_url(self):
        return '.'
