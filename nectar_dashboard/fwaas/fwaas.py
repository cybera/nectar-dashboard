# See openstack_dashboard/api/{nova,glance,swift}.py
# Also grep the main dashboard repo for 'nova.', 'glance.' and 'swift.' for usage examples

import xml.etree.ElementTree as ET
import time

from datetime import datetime
from xml.dom.minidom import parseString
from passlib.hash import md5_crypt

import requests
import requests.exceptions
import yaml

from openstack_dashboard.api import heat
from openstack_dashboard.api import nova
from openstack_dashboard.api import swift
from openstack_dashboard.api import glance
from horizon.exceptions import NotAvailable, NotAuthorized

DESTROY_CHECK_DELAY = 1
DESTROY_CHECK_ATTEMPTS = 10

class Status:
    NOT_RUNNING = "Not running"
    CREATE_IN_PROGRESS = "Creating"
    RUNNING = "Running"
    DELETE_IN_PROGRESS = "Deleting"
    UNKNOWN = "Unknown"

# Functions where return values matter are noted in the comments, other ones don't matter (for now)

def instance_exists(request):
    """ Return true if firewall instance is running, otherwise false """
    return get_instance(request) is not None

def instance_upgradeable(request):
    """ Return true if new firewall image is available, otherwise false """
    instance = get_instance(request)
    if instance is None:
        return False

    current_id = instance.image["id"]
    new_id = get_recent_image(request)
    if new_id is None:
        return False
    return current_id != new_id

def launch_instance(request, bootstrap=None, password=None):
    hot = swift.swift_get_object(request, "CyberaVFS", "hot.panos.yaml")
    env = swift.swift_get_object(request, "CyberaVFS", "env.panos.yaml")

    initcfg = swift.swift_get_object(request, "CyberaVFS", "init-cfg.txt").data.read().replace('\n', '\\n').strip()
    authcodes = swift.swift_get_object(request, "CyberaVFS", "authcodes").data.read().replace('\n', '\\n').strip()
    if bootstrap is None:
        bootstrap = swift.swift_get_object(request, "CyberaVFS", "bootstrap.xml").data.read()
    if password is not None:
        bootstrap = inject_phash(password, bootstrap)
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

def get_running_config(request, password):
    addr = get_ipv4_address(request)
    apikey = get_panos_api_key(request, password)

    resp = requests.get("https://%s//api/?type=export&category=configuration&key=%s" % (addr, apikey),
                        verify=False)
    resp.raise_for_status()

    return resp.text
    """
    Below is a possible alternative to the get_api_key function.
    It may be that we do not want to store the key, and if we can just
    use the basic auth, that would be better?
    return requests.get("https://%s//api/?type=export&category=configuration" % (addr),
                        auth=('CyberaVFS-api-account', password),
                        verify=False).text
    """

def create_backup(request, password, description):
    config = get_running_config(request, password)
    object_name = datetime.now().strftime("backup-%Y-%m-%d-%H:%M%S.xml")
    headers = {}
    headers['X-Object-Meta-Description'] = description
    swift.swift_api(request).put_object("CyberaVFS/backups", object_name, contents=config, headers=headers)

def get_backups(request):
    """ Return list of backup metadata (date, id) not the backups themselves """
    backups = []
    objects = swift.swift_get_objects(request, "CyberaVFS", "backups/")
    for o in objects[0]:
        headers = swift.swift_api(request).head_object("CyberaVFS", o['name'])
        backups.append({"id": o['name'], "date":o['last_modified'], "description": headers.get('x-object-meta-description', '')})
    return sorted(backups, key=lambda backup: backup["date"], reverse=True)

def recover_instance(request, backup_id, deact_key, password):
    bootstrap = swift.swift_get_object(request, "CyberaVFS", backup_id).data.read()
    delicense_instance(request, deact_key, password)
    destroy_instance(request)
    launch_instance(request, bootstrap)

def get_stack(request):
    filters = {
        'stack_name': 'cybera_virtual_firewall',
    }

    result = heat.stacks_list(request, filters=filters)
    stacks = result[0]
    if len(stacks) > 0:
        return stacks[0]

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

def get_panos_api_key(request, password):
    username = "CyberaVFS-api-account"
    addr = get_ipv4_address(request)
    r = requests.get("https://%s/api/?type=keygen&user=%s&password=%s" % (addr, username, password), verify=False)
    r.raise_for_status()
    x = parseString(r.text)
    apikey = x.getElementsByTagName('key')[0].childNodes[0].nodeValue
    return apikey

def delicense_instance(request, deact_key, password):
    apikey = get_panos_api_key(request, password)
    addr = get_ipv4_address(request)

    resp = requests.post("https://%s/api/?type=op&cmd=<request><license><api-key><set><key>%s</key></set></api-key></license></request>&key=%s" % (addr, deact_key, apikey), verify=False)
    resp.raise_for_status()

    resp = requests.post("https://%s/api/?type=op&cmd=<request><license><deactivate><key><mode>auto</mode></key></deactivate></license></request>&key=%s" % (addr, apikey), verify=False)
    resp.raise_for_status()

    for _ in range(10):
        resp = requests.get(
            "https://%s/api/?type=op&cmd=<show><system><info></info></system></show>&key=%s" % (addr, apikey),
            verify=False
        )
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            license = root.find("./result/system/vm-license").text
            if not license.startswith("VM-"):
                return
        time.sleep(1)

    raise NotAuthorized("Invalid deactivation key")

def destroy_instance(request):
    stack_id = get_stack(request).id
    heat.stack_delete(request, stack_id)

    for _ in range(DESTROY_CHECK_ATTEMPTS):
        if get_stack(request) is None:
            break
        time.sleep(DESTROY_CHECK_DELAY)

def upgrade_instance(request, deact_key, password):
    image_id = get_recent_image(request)
    if image_id is None:
        raise NotAvailable("No panos-production image available")
    update_image_id(request, image_id)
    config = get_running_config(request, password)
    delicense_instance(request, deact_key, password)
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

    if instance is None:
        return None

    for x in instance.addresses['default']:
        if x['version'] == 4:
            return x['addr']

def get_status(request):
    """
    Return current status of the stack
    """
    stack = get_stack(request)
    if stack is None:
        return Status.NOT_RUNNING

    check = stack.stack_status

    if check == 'CREATE_IN_PROGRESS':
        return Status.CREATE_IN_PROGRESS
    elif check == 'DELETE_IN_PROGRESS':
        return Status.DELETE_IN_PROGRESS
    elif check != 'CREATE_COMPLETE':
        return Status.UNKNOWN

    addr = get_ipv4_address(request)

    if addr is None:
        return Status.UNKNOWN

    resp = None
    try:
        resp = requests.get(
            "https://%s/api/?type=op&cmd=<show><system><info></info></system></show>" % (addr),
            verify=False
        )
    except requests.exceptions.RequestException:
        return Status.CREATE_IN_PROGRESS

    if resp.status_code != 403:
        return Status.UNKNOWN

    return Status.RUNNING

def inject_phash(password, bootstrap):
    """
    After the user creates a password for CyberaVFS-api-account it will need to be
    injected into bootstrap.xml
    """
    root = ET.fromstring(bootstrap)
    phash = root.find("./mgt-config/users/entry[@name='CyberaVFS-api-account']/phash")

    if phash is None:
        user = ET.fromstring('<entry name="CyberaVFS-api-account"><permissions><role-based><superuser>yes</superuser></role-based></permissions><phash></phash></entry>')
        users = root.find("./mgt-config/users")
        users.append(user)
        phash = root.find("./mgt-config/users/entry[@name='CyberaVFS-api-account']/phash")

    phash.text = md5_crypt.hash(password)
    return ET.tostring(root)
