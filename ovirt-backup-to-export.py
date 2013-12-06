#!/usr/bin/python
# Send all VMs to an Export Domain, forcing overwrite.
# Running VMs will be stopped and started again after export.

from ovirtsdk.xml import params
from ovirtsdk.api import API
import sys
import time

EXPORT_NAME = "EXPORT"
ENGINE_SERVER = "https://t420s.pahim.org"
ENGINE_USER = "admin@internal"
ENGINE_PASS = "admin"
ENGINE_CERT = "/etc/pki/ovirt-engine/ca.pem"

def Connect(url,username,password,ca_file):
    global api
    api = API(url = url,
              username = username,
              password = password,
              ca_file = ca_file)

def Disconnect(exitcode):
    api.disconnect()
    sys.exit(exitcode)

try:
    Connect(EXPORT_NAME,ENGINE_SERVER,ENGINE_USER,ENGINE_PASS,ENGINE_CERT)

    for vm in api.vms.list():
        previous_state = api.vms.get(vm.name).status.state

        print vm.name, previous_state

        if previous_state != 'down':
            print 'Shutting down VM %s' % vm.name
            api.vms.get(vm.name).shutdown()

        while api.vms.get(vm.name).status.state != 'down':
            print 'Waiting VM %s shutdown' % vm.name
            time.sleep(10)

        print 'Exporting VM %s' % vm.name
        api.vms.get(vm.name).export(params.Action(exclusive=True,force=True,async=False,storage_domain=api.storagedomains.get(EXPORT_NAME)))

        if previous_state == "up":
            print 'Starting back VM %s' % vm.name
            api.vms.get(vm.name).start()

    Disconnect(0)

except Exception as e:
    print 'Failed to export VM:\n%s' % str(e)
