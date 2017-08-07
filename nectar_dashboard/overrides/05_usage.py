from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from horizon import tables
from horizon.utils import filters
from openstack_dashboard import usage
from openstack_dashboard.dashboards.project.overview import views

from nectar_dashboard import helpers

# This is a local copy from openstack_dashboard.usage.
# Horizon breaks if this isn't here.
def get_instance_link(datum):
    view = "horizon:project:instances:detail"
    if datum.get('instance_id', False):
        return urlresolvers.reverse(view, args=(datum.get('instance_id'),))
    else:
        return None

# This overrides usage.ProjectUsage table to disable the CSV and Juju links
class CyberaProjectUsageTable(usage.BaseUsageTable):
    instance = tables.Column('name',
                             verbose_name=_("Instance Name"),
                             link=get_instance_link)
    uptime = tables.Column('uptime_at',
                           verbose_name=_("Time since created"),
                           filters=(filters.timesince_sortable,),
                           attrs={'data-type': 'timesince'})

    def get_object_id(self, datum):
        return datum.get('instance_id', id(datum))

    class Meta(object):
        name = "project_usage"
        hidden_title = False
        verbose_name = _("Usage")
        columns = ("instance", "vcpus", "disk", "memory", "uptime")
        table_actions = ()
        multi_select = False

# This enables our custom usage/quota calulcation to appear on the overview page.
class CyberaProjectOverview(views.ProjectOverview):
    table_class = CyberaProjectUsageTable
    usage_class = usage.ProjectUsage
    template_name = 'project/overview/usage.html'
    csv_response_class = views.ProjectUsageCsvRenderer

    def get_data(self):
	try:
	    project_id = self.kwargs.get('project_id', self.request.user.tenant_id)
	    self.usage = self.usage_class(self.request, project_id)
            self.usage.summarize(*self.usage.get_date_range())
            self.usage.limits = helpers.generate_limits(self.request)
            self.kwargs['usage'] = self.usage
        except Exception:
	    exceptions.handle(self.request, _('Unable to retrieve usage information.'))
            return []
	return self.usage.get_instances()

usage.ProjectUsageTable = CyberaProjectUsageTable
views.ProjectOverview = CyberaProjectOverview
