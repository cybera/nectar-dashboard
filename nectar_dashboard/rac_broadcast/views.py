from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from .forms import RACBroadcastForm

from nectar_dashboard import helpers
from . import utils
import logging
LOG = logging.getLogger(__name__)

class RACBroadcastView(forms.ModalFormView):
    form_class = RACBroadcastForm
    template_name = 'rac-broadcast/index.html'

    def get_success_url(self):
        return "."
