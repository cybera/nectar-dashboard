# See openstack_dashboard/api/{nova,glance,swift}.py
# Also grep the main dashboard repo for 'nova.', 'glance.' and 'swift.' for usage examples
from openstack_dashboard.api import nova
from openstack_dashboard.api import glance
from openstack_dashboard.api import swift


# Functions where return values matter are noted in the comments, other ones don't matter (for now)

def instance_exists(request):
    """ Return true if firewall instance is running, otherwise false """
    pass

def instance_upgradeable(request):
    """ Return true if new firewall image is available, otherwise false """
    pass

def launch_instance(request):
    pass

def create_backup(request):
    pass

def get_backups(request):
    """ Return list of backup metadata (date, id) not the backups themselves """
    backups = []
    backups.append({"id": 2, "date": "2017-09-06T17:32:16+00:0"})
    backups.append({"id": 1, "date": "2017-09-06T16:54:50+00:0"})
    return backups

def recover_instance(request, backup_id):
    """ backup_id is for you to decide on what it actually is """
    pass

def upgrade_instance(request):
    pass
