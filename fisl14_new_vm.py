#!/usr/bin/python
# ovirt-engine-sdk-3.3.0.3-1.20130514.gited3917b.fc18.noarch
# apahim AT redhat DOT com

from ovirtsdk.xml import params
from ovirtsdk.api import API
import sys
import getopt
import time
import re

MB = 1024 * 1024
GB = MB * 1024

def connect(url,username,password,ca_file):
    global api
    api = API(url = url,
              username = username,
              password = password,
              ca_file = ca_file)


def disconnect(exitcode):
    api.disconnect()
    sys.exit(exitcode)


def is_name_valid(newVmName):
    vms = api.vms.list()
    duplicated = False
    for vm in vms:
        if (vm.name == newVmName):
            duplicated = True

    if duplicated:
        return False
    else:
        return True


def create_vm(vm_name, vm_type, vm_mem, vm_cluster, vm_template):
    vm_params = params.VM(name=vm_name,
                          memory=vm_mem*MB,
                          cluster=api.clusters.get(name=vm_cluster),
                          template=api.templates.get(name=vm_template),
                          os=params.OperatingSystem(boot=[params.Boot(dev="hd")]))
    vm_params.set_type(vm_type)

    try:
        api.vms.add(vm=vm_params)
        print "Virtual machine '%s' added." % vm_name
    except Exception as ex:
        print "Adding virtual machine '%s' failed: %s" % (vm_name, ex)


def add_vm_nic(newVmName, nic_name, nic_iface, nic_net, nic_mac):
    vm = api.vms.get(newVmName)
    nic_name = nic_name
    nic_interface = nic_iface
    nic_network = api.networks.get(name=nic_net)
    nic_params = params.NIC(name=nic_name, interface=nic_interface, network=nic_network)

    try:
        nic = vm.nics.add(nic_params)
        nic.mac.set_address(nic_mac)
        nic.update()
        print "Network interface '%s' added to '%s'." % (nic.get_name(), vm.get_name())
    except Exception as ex:
        print "Adding network interface to '%s' failed: %s" % (vm.get_name(), ex)


def add_vm_disk(newVmName, disk_size, disk_type, disk_interface, disk_format, disk_bootable, disk_storage):
    vm = api.vms.get(newVmName)
    sd = params.StorageDomains(storage_domain=[api.storagedomains.get(name=disk_storage)])

    if disk_format == 'raw':
        sparse = 'false'
    elif disk_format == 'cow':
        sparse = 'true'

    disk_params = params.Disk(storage_domains=sd,
                              size=disk_size*GB,
                              type_=disk_type,
                              interface=disk_interface,
                              format=disk_format,
                              sparse=sparse,
                              bootable=disk_bootable)

    try:
        d = vm.disks.add(disk_params)
        print "Disk '%s' added to '%s'." % (d.get_name(), vm.get_name())
    except Exception as ex:
        print "Adding disk to '%s' failed: %s" % (vm.get_name(), ex)


def are_disks_ok(newVmName):
    vm = api.vms.get(newVmName)
    print 'Waiting all disks become available...'
    while True:
        waiting = False
        disks = vm.get_disks()
        for disk in disks.list():
            status = disk.get_status().get_state()
            if status == 'locked':
                waiting = True
                time.sleep(1)
        if not waiting:
            print ' [  OK  ] '
            break

    return True


def start_vm(newVmName):
    vm = api.vms.get(newVmName)
    if are_disks_ok(newVmName):
        try:
            vm.start()
            print "Started '%s'." % vm.get_name()
        except Exception as ex:
            print "Unable to start '%s': %s" % (vm.get_name(), ex)

def is_mac_valid(mac):
    if re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
        return True
    else:
        return False

def usage(msg):
    print msg
    print 'Usage: new-vm.py --vm-name=<new_vm_name> --mac <mac_address>'


if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:],"h",["help","vm-name=","mac="])
    for opt, arg in opts:
        if opt in ("-h","--help"):
            usage("Help:")
            sys.exit(0)
        elif opt in ("--vm-name"):
            newVmName = arg
        elif opt in ("--mac"):
            mac = arg

    if 'newVmName' not in vars():
        usage('What is the new vm Name?')
        sys.exit(1)

    if 'mac' not in vars():
        usage('What is the new vm MAC Address?')
        sys.exit(2)


    connect('https://engine.pahim.org',
            'admin@internal',
            'admin',
            '/etc/pki/ovirt-engine/ca.pem')

    if is_name_valid(newVmName):
        if is_mac_valid(mac):
            create_vm(newVmName, 'server', 512, 'Default', 'Blank')
            add_vm_nic(newVmName, 'nic1', 'virtio', 'ovirtmgmt', mac)
            add_vm_disk(newVmName, 50, 'system', 'virtio', 'cow', True, 'VMs')
            start_vm(newVmName)
            disconnect(0)
        else:
            usage('Sorry, MAC %s is  not valid.'% mac)
            disconnect(3)
    else:
        usage('Sorry, name %s is in use.'% newVmName)
        disconnect(2)

