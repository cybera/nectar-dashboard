from django.utils.translation import ugettext_lazy as _

import horizon


class RACQuotaChange(horizon.Panel):
    name = _("Quota Change")
    slug = 'quota_change'

    def allowed(self, context):
        return True
