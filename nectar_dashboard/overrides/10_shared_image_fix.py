from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.project.images import utils as image_utils

# This modifies the images.utils get_available_images to also retrieve shared
# images. This is to support the Horizon UI having shared images in the snapshot
# drop-down box when launching an instance. This is supported with the angular
# UIs, but we have angular disabled and there seems to be a bug with the
# non-angular UIs.
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

    # JT
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

    # JT
    #images = owned_images + public_images
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
