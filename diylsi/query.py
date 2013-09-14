import argparse, json, os, sys

def do_query():
    parser = argparse.ArgumentParser(prog='diy-lsi query', description='query diy-lsi db')
    parser.add_argument('-a', dest='all', help='print info for all', action='store_true')
    parser.add_argument('constraints', nargs='*', help='query constraints (key=value)')
    config = parser.parse_args(sys.argv[2:])

    hwdata = json.load(open('/etc/diy-lsi/hardware.js'))

    filters = {}
    if not config.all:
        for constraint in config.constraints:
            key, value = constraint.split('=')
            try:
                value = int(value)
            except:
                pass
            filters[key] = value 

    disks = [disk for disk in hwdata if False not in [disk.get(key, None) == value for key, value in filters.iteritems()]]
    for disk in disks:
        print disk
