#!/usr/bin/env python

import pymsn

import logging
import gobject

logging.basicConfig(level=logging.DEBUG)

finished = False
def get_proxies():
    import urllib
    proxies = urllib.getproxies()
    result = {}
    if 'https' not in proxies and \
            'http' in proxies:
        url = proxies['http'].replace("http://", "https://")
        result['https'] = pymsn.Proxy(url)
    for type, url in proxies.items():
        if type == 'no': continue
        result[type] = pymsn.Proxy(url)
    return result

class Client(pymsn.Client):
    def __init__(self, account, quit, http_mode=False):
        server = ('207.46.109.66', 1863)
        self.quit = quit
        if http_mode:
            from pymsn.transport import HTTPPollConnection
            pymsn.Client.__init__(self, server, account, get_proxies(), HTTPPollConnection)
        else:
            pymsn.Client.__init__(self, server, account, proxies = get_proxies())
        self.profile.connect("notify::presence", self.on_login_success)
        gobject.idle_add(self.connect)
        
    def connect(self):
        self.login()
        return False

    def on_connect_failure(self, proto):
        print "Connect failed"
        self.quit()

    def on_login_failure(self, proto):
        print "Login failed"
        self.quit()

    def on_login_success(self, proto):
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        #self.profile.presence = pymsn.Presence.ONLINE
        
def main():
    import sys
    import getpass
    import signal
    
    if "--http" in sys.argv:
        http_mode = True
        sys.argv.remove('--http')
    else:
        http_mode = False

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]
    
    if len(sys.argv) < 3:
        passwd = getpass.getpass('Password: ')
    else:
        passwd = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)

    def quit():
        mainloop.quit()

    def sigterm_cb():
        gobject.idle_add(quit)

    signal.signal(signal.SIGTERM, sigterm_cb)

    n = Client((account, passwd), quit, http_mode)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            quit()

if __name__ == '__main__':
    main()
