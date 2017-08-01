from django.utils.translation import ugettext_lazy as _

import horizon


class RACBroadcast(horizon.Panel):
    name = _("Broadcast")
    slug = 'rac_braodcast'

    def allowed(self, context):
        request = context['request']
        return request.user.has_perm('openstack.roles.admin')
