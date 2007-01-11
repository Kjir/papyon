import sys, os
parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir) 
del parent_dir
del sys
del os

import gnet
import gnet.protocol
import gobject

mainloop = gobject.MainLoop()

def sent(client, data, length):
    print '>>> Sent %d bytes' % length

def received(client, data, length):
    print '<<<', data

def status_change(client, param):
    if client.get_property('status') == gnet.constants.IoStatus.OPEN:
        c.send('GET / HTTP/1.1\r\nHost: localhost:9443\r\n\r\n')
    elif client.get_property('status') == gnet.constants.IoStatus.CLOSED:
        mainloop.quit()

c = gnet.io.SSLTCPClient('localhost', 9443)
c.connect("sent", sent)
c.connect("received", received)
c.connect("notify::status", status_change)

c.open()
mainloop.run()
