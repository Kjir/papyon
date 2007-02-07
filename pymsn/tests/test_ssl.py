import pymsn.gnet
import gobject

mainloop = gobject.MainLoop()

def sent(client, data, length):
    print '>>> Sent %d bytes' % length

def received(client, data, length):
    print '<<<', data

def status_change(client, param):
    if client.get_property('status') == pymsn.gnet.constants.IoStatus.OPEN:
        c.send('GET / HTTP/1.1\r\nHost: localhost:9443\r\n\r\n')
    elif client.get_property('status') == pymsn.gnet.constants.IoStatus.CLOSED:
        mainloop.quit()

c = pymsn.gnet.io.SSLTCPClient('localhost', 9443)
c.connect("sent", sent)
c.connect("received", received)
c.connect("notify::status", status_change)

c.open()
mainloop.run()
