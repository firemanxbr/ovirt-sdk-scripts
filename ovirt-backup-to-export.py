#!/usr/bin/python
from ovirtsdk.xml import params
from ovirtsdk.api import API
import sys
import time

EXPORT_NAME = "EXPORT"

def Connect(url,username,password,ca_file):
    global api
    api = API(url = url,
              username = username,
              password = password,
              ca_file = ca_file)

def Disconnect(exitcode):
    api.disconnect()
    sys.exit(exitcode)

Connect('https://t420s.pahim.org',
                'admin@internal',
                'admin',
                '/etc/pki/ovirt-engine/ca.pem')


try:
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

except Exception as e:
   print 'Failed to export VM:\n%s' % str(e)


Disconnect(0)
