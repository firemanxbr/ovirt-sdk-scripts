#!/usr/bin/python

import glob
import os
import tempfile
import subprocess
import logging
import sys

class OSName:
    UNKNOWN = 'unknown'
    OVIRT = 'oVirt Node'
    RHEL = 'RHEL'
    FEDORA = 'Fedora'
    RHEVH = 'RHEV Hypervisor'
    DEBIAN = 'Debian'


def mount(iso):
    iso_dir = tempfile.mkdtemp()
    squashfs_dir = tempfile.mkdtemp()
    ext3fs_dir = tempfile.mkdtemp()

    subprocess.check_call(["mount", "-o", "loop", iso, iso_dir])
    subprocess.check_call(["mount", iso_dir+"/LiveOS/squashfs.img", squashfs_dir])
    subprocess.check_call(["mount", squashfs_dir+"/LiveOS/ext3fs.img", ext3fs_dir])

    return iso_dir,squashfs_dir,ext3fs_dir


def umount(iso_dir,squashfs_dir,ext3fs_dir):
    subprocess.check_call(["umount", ext3fs_dir])
    subprocess.check_call(["umount", squashfs_dir])
    subprocess.check_call(["umount", iso_dir])

    os.removedirs(iso_dir)
    os.removedirs(squashfs_dir)
    os.removedirs(ext3fs_dir)

def _parseKeyVal(lines, delim='='):
    d = {}
    for line in lines:
        kv = line.split(delim, 1)
        if len(kv) != 2:
            continue
        k, v = map(str.strip, kv)
        d[k] = v
    return d

def getos(ext3fs_dir):
    if os.path.exists(ext3fs_dir+'/etc/rhev-hypervisor-release'):
        return OSName.RHEVH
    elif glob.glob(ext3fs_dir+'/etc/ovirt-node-*-release'):
        return OSName.OVIRT
    else:
        return OSName.UNKNOWN

def osversion(ext3fs_dir):
    version = release = ''

    osname = getos(ext3fs_dir)
    try:
        if osname == OSName.RHEVH or osname == OSName.OVIRT:
            d = _parseKeyVal(file(ext3fs_dir+'/etc/default/version'))
            version = d.get('VERSION', '')
            release = d.get('RELEASE', '')
    except:
        logging.error('failed to find version/release', exc_info=True)

    return dict(release=release, version=version, name=osname)


def isoversion(iso):
    iso_version = iso.split("-")[-2]
    iso_release = ".".join(iso.split("-")[-1].split(".")[:-1])

    return dict(release=iso_release, version=iso_version)

def compare(dict1, dict2):
    if dict1["release"] != dict2["release"]:
        return 1
    if dict1["version"] != dict2["version"]:
        return 2

    return 0

if __name__ == "__main__":
    if len(sys.argv) == 2:
        iso = sys.argv[1]
        iso_dir,squashfs_dir,ext3fs_dir = mount(iso)

        fs_data = osversion(ext3fs_dir)
        umount(iso_dir,squashfs_dir,ext3fs_dir)

        iso_data = isoversion(iso)

        if compare(fs_data, iso_data) is 0:
            print "SUCCESS!"
            print("FILENAME(engine probe) - version: %s, release: %s" % (iso_data["version"], iso_data["release"]))
            print("FYLESYSTEM(vdsm probe) -  version: %s, release: %s" % (fs_data["version"], fs_data["release"]))

        elif compare(fs_data, iso_data) is 1:
            print "ERROR - RELEASE MISMATCH"
            print("FILENAME(engine probe) - release: %s" % (iso_data["release"]))
            print("FYLESYSTEM(vdsm probe) -  release: %s" % (fs_data["release"]))

        elif compare(fs_data, iso_data) is 2:
            print "ERROR - VERSION MISMATCH"
            print("FILENAME(engine probe) - version: %s" % (iso_data["version"]))
            print("FYLESYSTEM(vdsm probe) -  version: %s" % (fs_data["version"]))

    else:
        print "Please provide the full iso path"
        sys.exit(0)

