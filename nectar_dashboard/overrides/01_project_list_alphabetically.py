import collections

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa
from horizon import forms as horizon_forms
from openstack_dashboard import api
from openstack_dashboard.dashboards.identity.projects import views as projects_views
from openstack_dashboard.dashboards.identity.users import forms as user_forms

PROJECT_REQUIRED = api.keystone.VERSIONS.active < 3
ADD_PROJECT_URL = "horizon:identity:projects:create"

# Sort admin Project list alphabetically
# This only patches the get_data method
class CyberaProjectView(projects_views.IndexView):
    def get_data(self):
        tenants = super(CyberaProjectView, self).get_data()
        tenants.sort(key=lambda x: x.name.lower())
        return tenants
projects_views.IndexView = CyberaProjectView

# When creating a user, sort the project list alphabetically
# This overwrites the original class. The entire original class must be copied and pasted here,
# then modifications can be done.
class CyberaCreateUserForm(user_forms.PasswordMixin, user_forms.BaseUserForm, user_forms.AddExtraColumnMixIn):
    # Hide the domain_id and domain_name by default
    domain_id = horizon_forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=horizon_forms.HiddenInput())
    domain_name = horizon_forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=horizon_forms.HiddenInput())
    name = horizon_forms.CharField(max_length=255, label=_("User Name"))
    description = horizon_forms.CharField(widget=horizon_forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    email = horizon_forms.EmailField(
        label=_("Email"),
        required=False)
    project = horizon_forms.ThemableDynamicChoiceField(label=_("Primary Project"),
                                               required=PROJECT_REQUIRED,
                                               add_item_link=ADD_PROJECT_URL)
    role_id = horizon_forms.ThemableChoiceField(label=_("Role"),
                                        required=PROJECT_REQUIRED)
    enabled = horizon_forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(CyberaCreateUserForm, self).__init__(*args, **kwargs)
        # Reorder form fields from multiple inheritance
        ordering = ["domain_id", "domain_name", "name",
                    "description", "email", "password",
                    "confirm_password", "project", "role_id",
                    "enabled"]
        self.add_extra_fields(ordering)
        self.fields = collections.OrderedDict(
            (key, self.fields[key]) for key in ordering)
        role_choices = [(role.id, role.name) for role in roles]
        self.fields['role_id'].choices = role_choices

        # For keystone V3, display the two fields in read-only
        if api.keystone.VERSIONS.active >= 3:
            readonlyInput = horizon_forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput
        # For keystone V2.0, hide description field
        else:
            self.fields["description"].widget = horizon_forms.HiddenInput()

        # jt
        # Sort project names
        self.fields['project'].choices.sort(key=lambda x: x[1])

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        domain = api.keystone.get_default_domain(self.request, False)
        try:
            LOG.info('Creating user with name "%s"' % data['name'])
            desc = data["description"]
            if "email" in data:
                data['email'] = data['email'] or None

            # add extra information
            if api.keystone.VERSIONS.active >= 3:
                EXTRA_INFO = getattr(settings, 'USER_TABLE_EXTRA_INFO', {})
                kwargs = dict((key, data.get(key)) for key in EXTRA_INFO)
            else:
                kwargs = {}

            new_user = \
                api.keystone.user_create(request,
                                         name=data['name'],
                                         email=data['email'],
                                         description=desc or None,
                                         password=data['password'],
                                         project=data['project'] or None,
                                         enabled=data['enabled'],
                                         domain=domain.id,
                                         **kwargs)
            messages.success(request,
                             _('User "%s" was successfully created.')
                             % data['name'])
            if data['project'] and data['role_id']:
                roles = api.keystone.roles_for_user(request,
                                                    new_user.id,
                                                    data['project']) or []
                assigned = [role for role in roles if role.id == str(
                    data['role_id'])]
                if not assigned:
                    try:
                        api.keystone.add_tenant_user_role(request,
                                                          data['project'],
                                                          new_user.id,
                                                          data['role_id'])
                    except Exception:
                        exceptions.handle(request,
                                          _('Unable to add user '
                                            'to primary project.'))
            return new_user
        except exceptions.Conflict:
            msg = _('User name "%s" is already used.') % data['name']
            messages.error(request, msg)
        except Exception:
            exceptions.handle(request, _('Unable to create user.'))
user_forms.CreateUserForm = CyberaCreateUserForm

# When updating a user's project, sort the project list alphabetically
# This overwrites the original class. The entire original class must be copied and pasted here,
# then modifications can be done.
class CyberaUpdateUserForm(user_forms.BaseUserForm, user_forms.AddExtraColumnMixIn):
    # Hide the domain_id and domain_name by default
    domain_id = horizon_forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=horizon_forms.HiddenInput())
    domain_name = horizon_forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=horizon_forms.HiddenInput())
    id = horizon_forms.CharField(label=_("ID"), widget=horizon_forms.HiddenInput)
    name = horizon_forms.CharField(max_length=255, label=_("User Name"))
    description = horizon_forms.CharField(widget=horizon_forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    email = horizon_forms.EmailField(
        label=_("Email"),
        required=False)
    project = horizon_forms.ThemableChoiceField(label=_("Primary Project"),
                                        required=PROJECT_REQUIRED)

    def __init__(self, request, *args, **kwargs):
        super(CyberaUpdateUserForm, self).__init__(request, *args, **kwargs)
        self.add_extra_fields()
        if api.keystone.keystone_can_edit_user() is False:
            for field in ('name', 'email'):
                self.fields.pop(field)
        # For keystone V3, display the two fields in read-only
        if api.keystone.VERSIONS.active >= 3:
            readonlyInput = horizon_forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput
        # For keystone V2.0, hide description field
        else:
            self.fields["description"].widget = horizon_forms.HiddenInput()

        # jt
        # Sort project names
        self.fields['project'].choices.sort(key=lambda x: x[1])

    def handle(self, request, data):
        user = data.pop('id')

        data.pop('domain_id')
	data.pop('domain_name')

        if not PROJECT_REQUIRED and 'project' not in self.changed_data:
            data.pop('project')

        if 'description' not in self.changed_data:
            data.pop('description')
        try:
            if "email" in data:
                data['email'] = data['email'] or None
            response = api.keystone.user_update(request, user, **data)
            messages.success(request,
                             _('User has been updated successfully.'))
        except exceptions.Conflict:
            msg = _('User name "%s" is already used.') % data['name']
            messages.error(request, msg)
            return False
        except Exception:
            response = exceptions.handle(request, ignore=True)
            messages.error(request, _('Unable to update the user.'))

        if isinstance(response, http.HttpResponse):
            return response
        else:
            return True
user_forms.UpdateUserForm = CyberaUpdateUserForm
