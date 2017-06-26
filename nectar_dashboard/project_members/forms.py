# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

# jt
from . import keystone as keystone_api

LOG = logging.getLogger(__name__)


class AddUserToProjectForm(forms.SelfHandlingForm):
    email = forms.EmailField(label=mark_safe("User's Rapid Access Cloud email address"),
                             required=True)

    def handle(self, request, data):
        project_id = request.user.tenant_id
        project_admin_user_id = request.user.id
        role = keystone_api.get_role_by_name(request, project_admin_user_id, project_id, "_member_")

        user = keystone_api.user_get_by_name(request, data['email'])
        keystone_api.add_tenant_user_role(request,
                                          project=project_id,
                                          user=user.id,
                                          role=role.id)
        messages.success(request,
                         _('User added successfully.'))
        return True
