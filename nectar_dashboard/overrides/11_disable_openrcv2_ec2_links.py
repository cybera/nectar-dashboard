from django.utils.translation import ugettext_lazy as _
from horizon import tables
from openstack_dashboard.dashboards.project.api_access import tables as api_tables

class CyberaEndpointsTable(tables.DataTable):
    api_name = tables.Column('type',
                             verbose_name=_("Service"),
                             filters=(api_tables.pretty_service_names,))
    api_endpoint = tables.Column('public_url',
                                 verbose_name=_("Service Endpoint"))

    class Meta(object):
        name = "endpoints"
        verbose_name = _("API Endpoints")
        multi_select = False
        # JT
        # Remove the openrcv2 and ec2 table actions from the list.
        table_actions = (
            api_tables.DownloadOpenRC,
            api_tables.ViewCredentials,
            api_tables.DownloadJujuEnv)
api_tables.EndpointsTable = CyberaEndpointsTable
