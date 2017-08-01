from openstack_dashboard.dashboards.project.instances import views as instances_views
from openstack_dashboard.dashboards.project.instances import tabs as instances_tabs

from django.core.urlresolvers import reverse
from horizon import tabs
from horizon.utils import memoized
from openstack_dashboard import api
from openstack_dashboard.utils import filters
from openstack_dashboard.dashboards.project.instances import tables as project_tables
from openstack_dashboard.dashboards.project.instances import tabs as project_tabs

import datetime
from dateutil import parser
from nectar_dashboard import helpers

# This overrides the entire project.instances.views.DetailView class
# This implements leasing extensions through the dashboard
# as well as hostId
class CyberaDetailView(tabs.TabView):
    tab_group_class = project_tabs.InstanceDetailTabs
    template_name = 'horizon/common/_detail.html'
    redirect_url = 'horizon:project:instances:index'
    page_title = "{{ instance.name|default:instance.id }}"
    image_url = 'horizon:project:images:images:detail'
    volume_url = 'horizon:project:volumes:volumes:detail'

    def get_context_data(self, **kwargs):
        context = super(CyberaDetailView, self).get_context_data(**kwargs)
        instance = self.get_data()
        if instance.image:
            instance.image_url = reverse(self.image_url,
                                         args=[instance.image['id']])
        instance.volume_url = self.volume_url
        context["instance"] = instance
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(instance)
        return context

    def _get_actions(self, instance):
        table = project_tables.InstancesTable(self.request)
        return table.render_row_actions(instance)

    @memoized.memoized_method
    def get_data(self):
        instance_id = self.kwargs['instance_id']

        try:
            instance = api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'instance "%s".') % instance_id,
                              redirect=redirect)
            # Not all exception types handled above will result in a redirect.
            # Need to raise here just in case.
            raise exceptions.Http302(redirect)

        choices = project_tables.STATUS_DISPLAY_CHOICES
        instance.status_label = (
            filters.get_display_label(choices, instance.status))

        try:
            instance.volumes = api.nova.instance_volumes_list(self.request,
                                                              instance_id)
            # Sort by device name
            instance.volumes.sort(key=lambda vol: vol.device)
        except Exception:
            msg = _('Unable to retrieve volume list for instance '
                    '"%(name)s" (%(id)s).') % {'name': instance.name,
                                               'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

        try:
            instance.full_flavor = api.nova.flavor_get(
                self.request, instance.flavor["id"])
        except Exception:
            msg = _('Unable to retrieve flavor information for instance '
                    '"%(name)s" (%(id)s).') % {'name': instance.name,
                                               'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

        try:
            instance.security_groups = api.network.server_security_groups(
                self.request, instance_id)
        except Exception:
            msg = _('Unable to retrieve security groups for instance '
                    '"%(name)s" (%(id)s).') % {'name': instance.name,
                                               'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

        try:
            api.network.servers_update_addresses(self.request, [instance])
        except Exception:
            msg = _('Unable to retrieve IP addresses from Neutron for '
                    'instance "%(name)s" (%(id)s).') % {'name': instance.name,
                                                        'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

        # jt - lease
        if helpers.is_leased_flavor(instance.full_flavor.name):
            project_id = self.request.user.tenant_id
            region = self.request.user.services_region
            instance.leased = True

            if self.request.GET.get('lease_time', False):
                lease_time = int(self.request.GET.get('lease_time'))
                new_lease = datetime.datetime.now() + datetime.timedelta(days=lease_time)
                helpers.set_instance_lease(instance.id, project_id, region, new_lease)

            lease_date = helpers.get_instance_lease(instance.id, project_id, region)
            if lease_date is None:
                lease_date = parser.parse(instance.created)+datetime.timedelta(days=1)
            instance.lease_date = lease_date
        else:
            instance.leased = False

        # jt - hostId
        i = api.nova.novaclient(self.request).servers.get(instance.id)
        instance.hostId = i.hostId

        return instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)


instances_views.DetailView = CyberaDetailView
