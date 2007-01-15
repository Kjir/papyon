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
    for type, url in proxies.items():
        if type == 'no': continue
        result[type] = pymsn.Proxy(url)
    return result

class Client(pymsn.Client):
    def __init__(self, account, quit):
        server = ('207.46.109.66', 1863)
        self.quit = quit
        pymsn.Client.__init__(self, server, account, proxies = get_proxies())
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
        self.profile.presence = pymsn.Presence.ONLINE

def main():
    import sys
    import getpass
    import signal

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

    n = Client((account, passwd), quit)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            quit()

if __name__ == '__main__':
    main()
