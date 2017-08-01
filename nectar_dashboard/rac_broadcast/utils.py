from openstack_dashboard import api

def get_admin_project_id(request):
    tenants = api.keystone.tenant_list(request)[0]
    admin_tenant_id = [tenant.id for tenant in tenants if tenant.name == 'admin'][0]
    return admin_tenant_id
