from django.utils.translation import ugettext_lazy as _

import horizon
from openstack_dashboard.dashboards.project import dashboard


class ApprovedRequests(horizon.Panel):
    name = _("Approved Requests")
    slug = 'approved_requests'
    index_url_name = 'approved_requests'
    permissions = ('openstack.roles.allocationadmin',)


dashboard.Project.register(ApprovedRequests)
