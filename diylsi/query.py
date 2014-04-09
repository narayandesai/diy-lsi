import argparse, json, os, sys

def run_query(path, constraints):
    hwdata = json.load(open(path))
    filters = {}
    for key, val in constraints:
        filters[key] = val
    return [item for item in hwdata if False not in [item.get(key, None) == value for key, value in filters.iteritems()]]

class Matcher():
    def __init__(self, name, description, callback):
        self.parser = argparse.ArgumentParser(prog='diy-lsi %s' % name, description=description)
        self.parser.add_argument('constraints', nargs='*', help='query constraints (key=value)')        
        self.callback = callback

    def run(self):
        config = self.parser.parse_args(sys.argv[2:])
        constraints = list()
        for constraint in config.constraints:
            key, value = constraint.split('=')
            try:
                value = int(value)
            except:
                pass
            constraints.append((key, value))

        for item in run_query('/etc/diy-lsi/hardware.js', constraints):
            self.callback(config, item)
  
def print_entry(_, entry):
    print entry

def do_query():
    m = Matcher('query', 'query cache db', print_entry)
    m.run()

class LEDMatcher(Matcher):
    def __init__(self, name, description):
        Matcher.__init__(self, name, description, self.light)
        self.parser.add_argument('-q', dest='q', help='query led state', action='store_true')
        self.parser.add_argument('-0', dest='off', help='disable drive leds', action='store_true')
        self.parser.add_argument('-1', dest='on', help='light drive leds', action='store_true')

    def light(self, config, entry):
        if len([x for x in entry.keys() if x in ['ctrl', 'slot', 'enclosure']]) != 3:
            print "Malformed entry :%s: for id" % entry
            return
        if config.on:
            mode = 'on'
        elif config.off:
            mode = 'off'
        os.popen("sas2ircu %s LOCATE %d:%d %s" % (entry['ctrl'], entry['enclosure'], entry['slot'], mode)).read()

def do_id():
    L = LEDMatcher('id', 'set LED state')
    L.run()
