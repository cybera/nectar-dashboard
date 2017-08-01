from openstack_dashboard import views as openstack_dashboard_views

import horizon
from horizon import exceptions

# This is a copy/paste of openstack_dashboard.views.get_user_home
# with modifications made.
def cybera_get_user_home(user):
    try:
        token = user.token
    except AttributeError:
        raise exceptions.NotAuthenticated()
    # Domain Admin, Project Admin will default to identity
    if token.project.get('id') is None or user.is_superuser:
        try:
            # jt
            #dashboard = horizon.get_dashboard('identity')
            dashboard = horizon.get_dashboard('project')
        except base.NotRegistered:
            pass
    else:
        dashboard = horizon.get_default_dashboard()

    return dashboard.get_absolute_url()

openstack_dashboard_views.get_user_home = cybera_get_user_home
