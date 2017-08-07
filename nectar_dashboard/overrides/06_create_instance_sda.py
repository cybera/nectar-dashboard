from django.conf import settings
from horizon import workflows
from openstack_dashboard.dashboards.project.instances import views
from openstack_dashboard.dashboards.project.instances import workflows as project_workflows

# This is a full override of project.instances.views.LaunchInstanceView
class CyberaLaunchInstanceView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchInstance

    def get_initial(self):
        initial = super(CyberaLaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        defaults = getattr(settings, 'LAUNCH_INSTANCE_DEFAULTS', {})
        initial['config_drive'] = defaults.get('config_drive', False)
	initial['device_name'] = 'sda'
        return initial

views.LaunchInstanceView = CyberaLaunchInstanceView
