import json
import logging

import django
from django.conf import settings
from django.utils import html
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from oslo_utils import strutils

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.stacks import forms as stacks_forms
from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils

LOG = logging.getLogger(__name__)

def volume_field_data(request, include_empty_option=False):
    """Returns a list of tuples of all volumes."""

    volume_list = []
    try:
        volumes = api.cinder.volume_list(request)
        volume_list = [(volume.id, volume.name) for volume in volumes if len(volume.attachments) == 0]
    except Exception:
        exceptions.handle(request, _('Unable to retrieve volumes.'))

    if not volume_list:
        if include_empty_option:
            return [("", _("No volumes available")), ]
        return []

    if include_empty_option:
        return [("", _("Select a volume")), ] + volume_list
    return volume_list

class CyberaCreateStackForm(forms.SelfHandlingForm):

    param_prefix = '__param_'

    class Meta(object):
        name = _('Create Stack')

    environment_data = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    if django.VERSION >= (1, 9):
        # Note(Itxaka): On django>=1.9 Charfield has an strip option that
        # we need to set to False as to not hit
        # https://bugs.launchpad.net/python-heatclient/+bug/1546166
        environment_data.strip = False

    parameters = forms.CharField(
        widget=forms.widgets.HiddenInput)
    stack_name = forms.RegexField(
        max_length=255,
        label=_('Stack Name'),
        help_text=_('Name of the stack to create.'),
        regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
        error_messages={'invalid':
                        _('Name must start with a letter and may '
                          'only contain letters, numbers, underscores, '
                          'periods and hyphens.')})
    timeout_mins = forms.IntegerField(
        initial=60,
        label=_('Creation Timeout (minutes)'),
        help_text=_('Stack creation timeout in minutes.'))
    enable_rollback = forms.BooleanField(
        label=_('Rollback On Failure'),
        help_text=_('Enable rollback on create/update failure.'),
        required=False)

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop('parameters')
        # special case: load template data from API, not passed in params
        if kwargs.get('validate_me'):
            parameters = kwargs.pop('validate_me')
        super(CyberaCreateStackForm, self).__init__(*args, **kwargs)

        if self._stack_password_enabled():
            self.fields['password'] = forms.CharField(
                label=_('Password for user "%s"') % self.request.user.username,
                help_text=_('This is required for operations to be performed '
                            'throughout the lifecycle of the stack'),
                widget=forms.PasswordInput())

        self._build_parameter_fields(parameters)

    def _stack_password_enabled(self):
        stack_settings = getattr(settings, 'OPENSTACK_HEAT_STACK', {})
        return stack_settings.get('enable_user_pass', True)

    def _build_parameter_fields(self, template_validate):
        self.help_text = template_validate['Description']

        params = template_validate.get('Parameters', {})
        if template_validate.get('ParameterGroups'):
            params_in_order = []
            for group in template_validate['ParameterGroups']:
                for param in group.get('parameters', []):
                    if param in params:
                        params_in_order.append((param, params[param]))
        else:
            # no parameter groups, simply sorted to make the order fixed
            params_in_order = sorted(params.items())
        for param_key, param in params_in_order:
            field = None
            field_key = self.param_prefix + param_key
            field_args = {
                'initial': param.get('Default', None),
                'label': param.get('Label', param_key),
                'help_text': html.escape(param.get('Description', '')),
                'required': param.get('Default', None) is None
            }

            param_type = param.get('Type', None)
            hidden = strutils.bool_from_string(param.get('NoEcho', 'false'))
            if 'CustomConstraint' in param:
                choices = self._populate_custom_choices(
                    param['CustomConstraint'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif 'AllowedValues' in param:
                choices = map(lambda x: (x, x), param['AllowedValues'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif param_type == 'Json' and 'Default' in param:
                field_args['initial'] = json.dumps(param['Default'])
                field = forms.CharField(**field_args)

            elif param_type in ('CommaDelimitedList', 'String', 'Json'):
                if 'MinLength' in param:
                    field_args['min_length'] = int(param['MinLength'])
                    field_args['required'] = field_args['min_length'] > 0
                if 'MaxLength' in param:
                    field_args['max_length'] = int(param['MaxLength'])
                if hidden:
                    field_args['widget'] = forms.PasswordInput(
                        render_value=True)
                field = forms.CharField(**field_args)

            elif param_type == 'Number':
                if 'MinValue' in param:
                    field_args['min_value'] = int(param['MinValue'])
                if 'MaxValue' in param:
                    field_args['max_value'] = int(param['MaxValue'])
                field = forms.IntegerField(**field_args)

            elif param_type == 'Boolean':
                field_args['required'] = False
                field = forms.BooleanField(**field_args)

            if field:
                self.fields[field_key] = field

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in data.items()
                       if k.startswith(self.param_prefix)]
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'files': json.loads(data.get('parameters')).get('files'),
            'template': json.loads(data.get('parameters')).get('template')
        }
        if data.get('password'):
            fields['password'] = data.get('password')

        if data.get('environment_data'):
            fields['environment'] = data.get('environment_data')

        try:
            api.heat.stack_create(self.request, **fields)
            messages.info(request, _("Stack creation started."))
            return True
        except Exception:
            exceptions.handle(request)

    def _populate_custom_choices(self, custom_type):
        if custom_type == 'neutron.network':
            return instance_utils.network_field_data(self.request, True)
        if custom_type == 'nova.keypair':
            return instance_utils.keypair_field_data(self.request, True)
        if custom_type == 'glance.image':
            return image_utils.image_field_data(self.request, True)
        if custom_type == 'nova.flavor':
            return instance_utils.flavor_field_data(self.request, True)
        if custom_type == 'cinder.volume':
            return volume_field_data(self.request, True)
        return []

stacks_forms.CreateStackForm = CyberaCreateStackForm
