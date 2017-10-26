from django.utils.translation import ugettext_lazy as _

import horizon

class Fwaas(horizon.Panel):
    name = _("CyberaVFS")
    slug = 'fwaas'

    def allowed(self, context):
        return True
        request = context['request']
        for role in request.user.roles:
            if role['name'] == 'CyberaVFS':
                return True
        return False
