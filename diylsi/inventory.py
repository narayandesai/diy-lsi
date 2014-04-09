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

mptre = '\s+devhdl (?P<sas_target>[0-9a-f]+), sasaddress (?P<guid>[0-9a-f]+),'

def parse_mdb_mpt():
    ret = list()
    data = os.popen('echo ::mptsas -t | mdb -k').read()
    for dev in re.finditer(mptre, data):
        devinfo = dev.groupdict()
        devinfo['sas_target'] = int(devinfo['sas_target'], 16)
        ret.append(devinfo)
    return ret

diskre = '''Device is a Hard disk
\s+Enclosure #                             : (?P<enclosure>\d+)
\s+Slot #                                  : (?P<slot>\d+)
\s+SAS Address                             : (?P<sas_address>[0-9a-f\-]+)
\s+State                                   : (?P<state>[A-Za-z \(\)]+)
\s+Size \(in MB\)/\(in sectors\) +: (?P<size>\d+)/(?P<sectors>\d+)
\s+Manufacturer +: (?P<manufacturer>[^\n]+)
\s+Model Number +: (?P<model>[^\n]+)
\s+Firmware Revision +: (?P<firmware>[^\n]+)
\s+Serial No +: (?P<serial>\S+)
\s+GUID +: (?P<guid>\S+)
\s+Protocol +: (?P<protocol>\S+)
\s+Drive Type +: (?P<drivetype>\S+)
'''

encre = '''Device is a Enclosure services device
  Enclosure #                             : (?P<enclosure>\d+)
  Slot #                                  : (?P<slot>\d+)
  SAS Address                             : (?P<sas_address>[0-9a-f\-]+)
  State                                   : (?P<state>[A-Za-z \(\)]+)
  Manufacturer                            : (?P<manufacturer>[^\n]+)
\s+Model Number +: (?P<model>[^\n]+)
\s+Firmware Revision +: (?P<firmware>[^\n]+)
\s+Serial No +: (?P<serial>\S+)
\s+GUID +: (?P<guid>\S+)
\s+Protocol +: (?P<protocol>\S+)
\s+Device Type +: (?P<devtype>\S+)'''

def probe_lsi_controller(ctrl):
    ret = list()
    data = os.popen('''sas2ircu %d display''' % ctrl).read()
    dtemplate = {'type': 'disk', 'ctrl': ctrl}
    enctemplate = {'type':'enclosure', 'ctrl': ctrl}
    for disk in re.finditer(diskre, data):
        diskinfo = disk.groupdict()
        diskinfo.update(dtemplate)
        diskinfo['serial'] = diskinfo['serial'][:15]
        for key in ['size', 'sectors', 'slot', 'enclosure']:
            diskinfo[key] = int(diskinfo[key])
        ret.append(diskinfo)
    for enclosure in re.finditer(encre, data):
        encdata = enclosure.groupdict()
        encdata.update(enctemplate)
        encdata['model'] = encdata['model'].strip()
        encdata['guid'] = encdata['sas_address'].replace('-', '')
        ret.append(encdata)
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


