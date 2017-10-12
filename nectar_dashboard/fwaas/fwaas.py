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
    search_opts = {
        'name': '^cybera_virtual_firewall$',
    }

    result = nova.server_list(request, search_opts)
    instance = result[0]
    if len(instance) > 0:
        return True

    return False

def instance_upgradeable():
    """ Return true if new firewall image is available, otherwise false """
    pass

def launch_instance(request):
    initcfg = swift.swift_get_object(request, "CyberaVFS", "init-cfg.txt").data.read().replace('\n', '\\n').strip()
    hot = swift.swift_get_object(request, "CyberaVFS", "hot.panos.yaml")
    env = swift.swift_get_object(request, "CyberaVFS", "env.panos.yaml")

    tpl = hot.data.read()
    tpl = tpl.replace('%INITCFG%', initcfg)

    fields = {
        'environment': env.data.read(),
        'template': tpl,
        'stack_name': 'cybera_virtual_firewall',
        'timeout_mins': 10,
    }

    heat.stack_create(request, **fields)


def create_backup(request):
    username = "foo"
    password = "foo"

    search_opts = {
        'name': '^cybera_virtual_firewall$',
    }

    result = nova.server_list(request, search_opts)
    instance = result[0][0]
    addr = instance.addresses['mgmt'][0]['addr']
    r = requests.get("https://%s/api/?type=keygen&user=%s&password=%s" % (addr, username, password), verify=False)
    x = parseString(r.text)
    apikey = x.getElementsByTagName('key')[0].childNodes[0].nodeValue

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

def recover_instance(backup_id):
    """ backup_id is for you to decide on what it actually is """
    pass

def upgrade_instance():
    pass
