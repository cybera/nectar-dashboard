from django.utils.translation import ugettext_lazy as _

import horizon

class Fwaas(horizon.Panel):
    name = _("FWaaS")
    slug = 'fwaas'

    def allowed(self, context):
        return True
        request = context['request']
        for role in request.user.roles:
            if role['name'] == 'FWaaS':
                return True
        return False
