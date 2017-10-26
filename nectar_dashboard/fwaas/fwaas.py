# See openstack_dashboard/api/{nova,glance,swift}.py
# Also grep the main dashboard repo for 'nova.', 'glance.' and 'swift.' for usage examples

from datetime import datetime
from xml.dom.minidom import parseString

import time
import requests
import yaml

from openstack_dashboard.api import heat
from openstack_dashboard.api import nova
from openstack_dashboard.api import swift
from openstack_dashboard.api import glance
from horizon.exceptions import NotAvailable

DESTROY_CHECK_DELAY = 1
DESTROY_CHECK_ATTEMPTS = 10


# Functions where return values matter are noted in the comments, other ones don't matter (for now)

def instance_exists(request):
    """ Return true if firewall instance is running, otherwise false """
    return get_instance(request) is not None

def instance_upgradeable(request):
    """ Return true if new firewall image is available, otherwise false """
    current_id = get_instance(request).image["id"]
    new_id = get_recent_image(request)
    if new_id is None:
        return False
    return current_id != new_id

def launch_instance(request, bootstrap=None):
    hot = swift.swift_get_object(request, "CyberaVFS", "hot.panos.yaml")
    env = swift.swift_get_object(request, "CyberaVFS", "env.panos.yaml")

    initcfg = swift.swift_get_object(request, "CyberaVFS", "init-cfg.txt").data.read().replace('\n', '\\n').strip()
    authcodes = swift.swift_get_object(request, "CyberaVFS", "authcodes").data.read().replace('\n', '\\n').strip()
    if bootstrap is None:
        bootstrap = swift.swift_get_object(request, "CyberaVFS", "bootstrap.xml").data.read()
    bootstrap = bootstrap.replace('"', "'").replace('\n', '\\n').strip()

    tpl = hot.data.read()
    tpl = tpl.replace('%INITCFG%', initcfg)
    tpl = tpl.replace('%BOOTSTRAP%', bootstrap)
    tpl = tpl.replace('%AUTHCODES%', authcodes)

    fields = {
        'environment': env.data.read(),
        'template': tpl,
        'stack_name': 'cybera_virtual_firewall',
        'timeout_mins': 10,
    }

    heat.stack_create(request, **fields)

def get_running_config(request):
    addr = get_ipv4_address(request)
    apikey = get_panos_api_key(request)

    return requests.get("https://%s//api/?type=export&category=configuration&key=%s" % (addr, apikey), verify=False).text

def create_backup(request):
    config = get_running_config(request)
    object_name = datetime.now().strftime("backup-%Y-%m-%d-%H:%M%S.xml")
    swift.swift_api(request).put_object("CyberaVFS/backups", object_name, contents=config)

def get_backups(request):
    """ Return list of backup metadata (date, id) not the backups themselves """
    backups = []
    objects = swift.swift_get_objects(request, "CyberaVFS", "backups/")
    for o in objects[0]:
        backups.append({"id": o['name'], "date":o['last_modified']})
    return reversed(backups)

def recover_instance(request, backup_id, deact_key):
    bootstrap = swift.swift_get_object(request, "CyberaVFS", backup_id).data.read()
    delicense_instance(request, deact_key)
    destroy_instance(request)
    launch_instance(request, bootstrap)

def get_stack_id(request):
    filters = {
        'stack_name': 'cybera_virtual_firewall',
    }

    result = heat.stacks_list(request, filters=filters)
    stacks = result[0]
    if len(stacks) > 0:
        return stacks[0].id

    return None

def get_instance(request):
    search_opts = {
        'name': '^cybera_virtual_firewall$',
    }

    result = nova.server_list(request, search_opts)
    instances = result[0]
    if len(instances) > 0:
        return instances[0]

    return None

def get_panos_api_key(request):
    username = "foo"
    password = "bar"
    addr = get_ipv4_address(request)
    r = requests.get("https://%s/api/?type=keygen&user=%s&password=%s" % (addr, username, password), verify=False)
    x = parseString(r.text)
    apikey = x.getElementsByTagName('key')[0].childNodes[0].nodeValue
    return apikey

def delicense_instance(request, deact_key):
    apikey = get_panos_api_key(request)
    addr = get_ipv4_address(request)
    requests.post("https://%s/api/?type=op&cmd=<request><license><api-key><set><key>%s</key></set></api-key></license></request>&key=%s" % (addr, deact_key, apikey), verify=False)
    requests.post("https://%s/api/?type=op&cmd=<request><license><deactivate><key><mode>auto</mode></key></deactivate></license></request>&key=%s" % (addr, apikey), verify=False)
    time.sleep(10)

def destroy_instance(request):
    stack_id = get_stack_id(request)
    heat.stack_delete(request, stack_id)

    for _ in range(DESTROY_CHECK_ATTEMPTS):
        if get_stack_id(request) is None:
            break
        time.sleep(DESTROY_CHECK_DELAY)

def upgrade_instance(request, deact_key):
    image_id = get_recent_image(request)
    if image_id is None:
        raise NotAvailable("No panos-production image available")
    update_image_id(request, image_id)
    config = get_running_config(request)
    delicense_instance(request, deact_key)
    destroy_instance(request)
    launch_instance(request, config)


def update_image_id(request, image_id):
    env = swift.swift_get_object(request, "CyberaVFS", "env.panos.yaml").data.read()
    env = yaml.load(env)
    env['parameters']['image'] = image_id
    env = yaml.safe_dump(env)
    swift.swift_api(request).put_object("CyberaVFS", "env.panos.yaml", contents=env)

def get_recent_image(request):
    filters = {
        'name': 'panos-production',
    }

    result = glance.image_list_detailed(request, filters=filters)
    images = result[0]
    for image in images:
        if image.owner != request.user.tenant_id:
            return image.id

    return None

def get_ipv4_address(request):
    instance = get_instance(request)
    for x in instance.addresses['default']:
        if x['version'] == 4:
            return x['addr']
