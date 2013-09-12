#!/usr/bin/env python

import json, multiprocessing, os, re, sys

def join_dict(a, b, field):
    new = dict()
    unmatched = list()
    for item in a + b:
        if field not in item:
            unmatched.append(item)
            continue
        if item[field] in new:
            new[item[field]].update(item)
        else:
            new[item[field]] = item
    return new.values() + unmatched

def parse_mdb_mpt():
    ret = list()
    for target in [item.replace(',', '').split() for item in os.popen('echo ::mptsas -t | mdb -k | grep devhdl').readlines()]:
        ret.append({'guid':target[3], 'sas_target': int(target[1], 16)})
    return ret

def probe_lsi_controller(ctrl):
    ret = list()
    data = [x for x in os.popen('''sas2ircu %s display | grep -A12 "Device is a Hard disk" | grep -v "is a Hard disk"''' % (ctrl)).readlines() if x != '--\n']
    num_disks = len(data)/12
    for disk in range(num_disks):
        diskinfo = {'controller': ctrl}
        base_idx = disk*12
        disk_data = [item.split() for item in data[base_idx:base_idx+12]]
        for entry in disk_data:
            if entry[0] == 'Enclosure':
                diskinfo['enclosure'] = int(entry[3])
            elif entry[0] == 'Slot':
                diskinfo['slot'] = int(entry[3])
            elif entry[0:2] == ['SAS', 'Address']:
                diskinfo['sas_address'] = entry[3]
            elif entry[0:2] == ['Serial', 'No']:
                diskinfo['serial'] = entry[3][:15]
            elif entry[0] == 'GUID':
                diskinfo['guid'] = entry[2]
            else:
                pass
        ret.append( diskinfo)
    return ret

def parse_sas2ircu():
    data = [x for x in os.popen("sas2ircu list | grep -A2 Index").readlines() if x != '--\n']
    num_ctrl = len(data)/3
    p = multiprocessing.Pool(12)
    results = p.map(probe_lsi_controller, range(num_ctrl))
    return reduce(lambda x,y:x+y, results)

def parse_iostat():
    pattern = re.compile('.*Serial No: (\S+) Size')
    ret = list()
    cmd = os.popen("iostat -En")
    while True:
        data = cmd.readline().split() + cmd.readline().split() + cmd.readline().split() + cmd.readline().split() + cmd.readline().split()
        if not data:
            break
        ret.append({'name': data[0], 'serial': pattern.match(' '.join(data)).group(1)})
    return ret

def parse_zpool():
    ret = list()
    vd_types = ['raidz', 'mirror']
    skiplist = ['replacing', 'errors:']
    pool = None
    config = False
    skip = False
    vdev = None
    for line in os.popen("zpool status").readlines():
        if len(line.split()) == 0:
            continue
        if skip:
           skip = False
           continue
        if line.split()[0] == 'pool:':
            pool = line.split()[1]
            config = False
        elif line.split()[0] == 'NAME':
            config = True
            skip = True
        elif config:
            vd_info = [x for x in vd_types if line.split()[0].startswith(x)]
            if vd_info:
                vdev = line.split()[0]
                continue
            elif [x for x in skiplist if line.split()[0].startswith(x)]:
                continue
            # need to truncate device name at 22 characters
            ret.append({'name': line.split()[0][:21], 'pool':pool, 'vdev':vdev, 'zfs_state':line.split()[1]})
        else:
            pass
    return ret


