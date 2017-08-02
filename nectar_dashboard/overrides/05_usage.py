from openstack_dashboard import usage
from openstack_dashboard.dashboards.project.overview import views

from nectar_dashboard import helpers

class CyberaProjectOverview(views.ProjectOverview):
    usage_class = usage.ProjectUsage
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

views.ProjectOverview = CyberaProjectOverview
