#!/usr/bin/python
# ovirt 3.2

from ovirtsdk.xml import params
from ovirtsdk.api import API
import sys
import getopt
import time

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


def create_vm(newVmName, mem, cluster, template):
    vm_name = newVmName
    vm_memory = mem * MB
    vm_cluster = api.clusters.get(name=cluster)
    vm_template = api.templates.get(name=template)
    vm_os = params.OperatingSystem(boot=[params.Boot(dev="hd")])
    vm_params = params.VM(name=vm_name,
                         memory=vm_memory,
                         cluster=vm_cluster,
                         template=vm_template,
                         os=vm_os)

    try:
        api.vms.add(vm=vm_params)
        print "Virtual machine '%s' added." % vm_name
    except Exception as ex:
        print "Adding virtual machine '%s' failed: %s" % (vm_name, ex)


def add_vm_nic(newVmName, nic_name, nic_iface, nic_net):
    vm = api.vms.get(newVmName)
    nic_name = nic_name
    nic_interface = nic_iface
    nic_network = api.networks.get(name=nic_net)
    nic_params = params.NIC(name=nic_name, interface=nic_interface, network=nic_network)

    try:
        nic = vm.nics.add(nic_params)
        print "Network interface '%s' added to '%s'." % (nic.get_name(), vm.get_name())
    except Exception as ex:
        print "Adding network interface to '%s' failed: %s" % (vm.get_name(), ex)


def add_vm_disk(newVmName, disk_size, disk_type, disk_iface, disk_format, bootable):
    vm = api.vms.get(newVmName)
    sd = params.StorageDomains(storage_domain=[api.storagedomains.get(name="vms")])
    disk_size = disk_size * GB
    disk_type = disk_type 
    disk_interface = disk_iface 
    disk_format = disk_format
    disk_bootable = bootable

    disk_params = params.Disk(storage_domains=sd,
                              size=disk_size,
                              type_=disk_type,
                              interface=disk_interface,
                              format=disk_format,
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


def usage(msg):
    print msg
    print 'Usage: new-vm.py -n <new_vm_name>'


if __name__ == "__main__":
    connect('https://engine.pahim.org',
            'admin@internal',
            '0v1rt',
            '/etc/pki/ovirt-engine/ca.pem')
    opts, args = getopt.getopt(sys.argv[1:],"hn:",["new-vm-name="])
    for opt, arg in opts:
        if opt == '-h':
            usage("HELP:")
            disconnect(0)
        elif opt in ("-n", "--new-vm-name"):
            newVmName = arg
            if is_name_valid(newVmName):
                create_vm(newVmName, 512, 'Default', 'Blank')
                add_vm_nic(newVmName, 'nic1', 'virtio', 'rhevm')
                add_vm_disk(newVmName, 50, 'system', 'virtio', 'cow', True)
                start_vm(newVmName)
                disconnect(0)
            else:
                usage('Sorry, name %s is in use.'% newVmName)
                disconnect(2)

    if 'newVmName' not in vars():
        usage('What is the new vm name?')
        disconnect(1)
