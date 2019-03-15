from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import workflows
from horizon import exceptions

from openstack_dashboard.api import glance

from openstack_dashboard.dashboards.project.instances import views
from openstack_dashboard.dashboards.project.instances import workflows as project_workflows
from openstack_dashboard.dashboards.project.images import utils as image_utils

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

def cybera_get_available_images(request, project_id=None, images_cache=None):
    """Returns a list of images that are public or owned by the given
    project_id. If project_id is not specified, only public images
    are returned.

    :param images_cache: An optional dict-like object in which to
     cache public and per-project id image metadata.

    """
    if images_cache is None:
        images_cache = {}
    public_images = images_cache.get('public_images', [])
    images_by_project = images_cache.get('images_by_project', {})
    shared_images = images_cache.get('shared_images', [])

    if 'shared_images' not in images_cache:
        shared = {"visibility": "shared",
                  "status": "active"}
        try:
            images, _more, _prev = glance.image_list_detailed(
                request, filters=shared)
            [shared_images.append(image) for image in images]
            images_cache['shared_images'] = shared_images
        except Exception:
            exceptions.handle(request,
                              _("Unable to retrieve shared images."))

    if 'public_images' not in images_cache:
        public = {"is_public": True,
                  "status": "active"}
        try:
            images, _more, _prev = glance.image_list_detailed(
                request, filters=public)
            [public_images.append(image) for image in images]
            images_cache['public_images'] = public_images
        except Exception:
            exceptions.handle(request,
                              _("Unable to retrieve public images."))

    # Preempt if we don't have a project_id yet.
    if project_id is None:
        images_by_project[project_id] = []

    if project_id not in images_by_project:
        owner = {"property-owner_id": project_id,
                 "status": "active"}
        try:
            owned_images, _more, _prev = glance.image_list_detailed(
                request, filters=owner)
            images_by_project[project_id] = owned_images
        except Exception:
            owned_images = []
            exceptions.handle(request,
                              _("Unable to retrieve images for "
                                "the current project."))
    else:
        owned_images = images_by_project[project_id]

    if 'images_by_project' not in images_cache:
        images_cache['images_by_project'] = images_by_project

    images = owned_images + public_images + shared_images

    image_ids = []
    final_images = []
    for image in images:
        if image.id not in image_ids and \
                image.container_format not in ('aki', 'ari'):
            image_ids.append(image.id)
            final_images.append(image)
    return final_images

image_utils.get_available_images = cybera_get_available_images
