# See openstack_dashboard/api/{nova,glance,swift}.py
# Also grep the main dashboard repo for 'nova.', 'glance.' and 'swift.' for usage examples

import base64
import requests
import yaml
import StringIO

from datetime import datetime
from xml.dom.minidom import parseString

from openstack_dashboard.api import heat
from openstack_dashboard.api import nova
from openstack_dashboard.api import swift
from oslo_serialization import jsonutils


# Functions where return values matter are noted in the comments, other ones don't matter (for now)

def instance_exists(request):
    """ Return true if firewall instance is running, otherwise false """
    return get_instance() is not None

def instance_upgradeable():
    """ Return true if new firewall image is available, otherwise false """
    pass

def launch_instance(request, bootstrap=None):
    initcfg = swift.swift_get_object(request, "CyberaVFS", "init-cfg.txt").data.read().replace('\n', '\\n').strip()
    hot = swift.swift_get_object(request, "CyberaVFS", "hot.panos.yaml")
    env = swift.swift_get_object(request, "CyberaVFS", "env.panos.yaml")
    if bootstrap is None:
       bootstrap = swift.swift_get_object(request, "CyberaVFS", bootstrap).data.read()

    tpl = hot.data.read()
    tpl = tpl.replace('%INITCFG%', initcfg)
    tpl = tpl.replace('%BOOTSTRAP%', bootstrap)

    fields = {
        'environment': env.data.read(),
        'template': tpl,
        'stack_name': 'cybera_virtual_firewall',
        'timeout_mins': 10,
    }

    heat.stack_create(request, **fields)


def create_backup(request):
    addr = get_instance().addresses['mgmt'][0]['addr']
    apikey = get_panos_api_key()

    r = requests.get("https://%s//api/?type=export&category=configuration&key=%s" % (addr, apikey), verify=False)

    object_name = datetime.now().strftime("backup-%Y-%m-%d-%H:%M%S.xml")
    x = swift.swift_api(request).put_object("CyberaVFS/backups", object_name, contents=r.text)


def get_backups(request):
    """ Return list of backup metadata (date, id) not the backups themselves """
    backups = []
    objects = swift.swift_get_objects(request, "CyberaVFS", "backups/")
    for o in objects[0]:
        backups.append({"id": o['name'], "date":o['last_modified']})
    return backups

def recover_instance(request, backup_id, deact_key):
    bootstrap = swift.swift_get_object(request, "CyberaVFS", backup_id)
    delicense_instance(deact_key)
    destroy_instance(request)
    launch_instance(request, bootstrap)

def get_stack_id(request):
    filters = {
        'name': '^cybera_virtual_firewall$',
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

def get_panos_api_key():
    username = "CyberaVFS-api-account"
    password = "topic.jockey.finland.acyclic"
    addr = get_instance().addresses['mgmt'][0]['addr']
    r = requests.get("https://%s/api/?type=keygen&user=%s&password=%s" % (addr, username, password), verify=False)
    x = parseString(r.text)
    apikey = x.getElementsByTagName('key')[0].childNodes[0].nodeValue
    return apikey

def delicense_instance(deact_key):
    apikey = get_panos_api_key()
    addr = get_instance().addresses['mgmt'][0]['addr']
    requests.post("https://%s/api/?type=op&cmd=<request><license><api-key><set><key>%s</key></set></api-key></license></request>&key=%s" % (addr, deact_key, apikey), verify=False)
    requests.post("https://%s/api/?type=op&cmd=<request><license><deactivate><key><mode>auto</mode></key></deactivate></license></request>&key=%s" % (addr, apikey), verify=False)

def destroy_instance(request):
    stack_id = get_stack_id(request)
    heat.stack_delete(request, stack_id)

def upgrade_instance():
    pass
