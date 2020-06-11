from horizon import forms

from .forms import RACBroadcastForm

import logging
LOG = logging.getLogger(__name__)


class RACBroadcastView(forms.ModalFormView):
    form_class = RACBroadcastForm
    template_name = 'rac-broadcast/index.html'

    def get_success_url(self):
        return "."
