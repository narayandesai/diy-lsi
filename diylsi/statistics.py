import argparse, json, multiprocessing, os, re, sys

# all functions in this library take a disk info dict as input

def poll_smart_status(diskinfo):
    data = os.popen("/opt/omni/sbin/smartctl -a -d sat,12 /devices/scsi_vhci/disk@g%s:a,raw |grep self-assess" % diskinfo['guid']).readlines()[0]
    #data = os.popen("/opt/omni/sbin/smartctl -a -d scsi /devices/scsi_vhci/disk@g%s:a,raw |grep self-assess" % diskinfo['guid']).readlines()[0]
    return {'name':diskinfo['name'], 'smart-status': data.strip().split(':')[-1].strip()}

iomap = {'Soft Errors':'soft', 'Transport Errors':'transport', 'Media Error':'media', 'Device Not Ready':'not-ready', 'No Device':'no-device', 'Recoverable':'recoverable', 'Illegal Request':'illegal', 'Predictive Failure Analysis':'predictive'}
def poll_iostat(diskinfo):
    data = " ".join([x.strip() for x in os.popen("iostat -En %s" % diskinfo['name']).readlines()])
    ret = dict([('name', diskinfo['name'])])
    for key, val in iomap.iteritems():
        match = re.compile('.*%s: (\d+)' % key).match(data)
        if match:
            ret[val] = int(match.group(1))
    return ret

def get_statistics(diskinfo):
    data = poll_smart_status(diskinfo)
    data.update(poll_iostat(diskinfo))
    return data

def filter_zero_stats(disklist):
    hard = ['transport', 'media', 'not-ready', 'no-device']
    nzdisks = list()
    for disk in disklist:
        if disk['smart-status'] != 'PASSED':
            nzdisks.append(disk)
            continue
        for field in hard:
            if disk[field] != 0:
                nzdisks.append(disk)
                continue
        if disk['soft'] != disk['recoverable']:
            nzdisks.append(disk)
            continue
    return nzdisks

def do_statistics():
    parser = argparse.ArgumentParser(prog='diy-lsi stats',
                                     description='disk statistics info')
    parser.add_argument('-z', dest='zero', help='display non-zero counters', action='store_true', default=False)
    parser.add_argument('disks', help='disk name', nargs='*')
    config = parser.parse_args(sys.argv[2:])
    hwdb = json.load(open('/etc/diy-lsi/hardware.js'))
    if config.disks:
        disks = [x for x in hwdb if x.get('name') in config.disks]
    else:
        disks = [x for x in hwdb if x.has_key('name') and x.has_key('guid')]
    pool = multiprocessing.Pool(64)
    results = pool.map(get_statistics, disks)
    if config.zero:
        results = filter_zero_stats(results)
    for stat in results:
        print stat
