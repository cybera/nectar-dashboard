from django.utils.translation import ugettext_lazy as _

import horizon

project = horizon.get_dashboard("project")
data_processing = project.get_panel_group("data_processing")
for i in data_processing:
    i.permissions = ('openstack.roles.sahara_user',)
