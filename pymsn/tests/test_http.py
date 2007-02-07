import pymsn.gnet
import pymsn.gnet.protocol
import gobject

mainloop = gobject.MainLoop()

def response(http, resp):
    global mainloop
    print resp.reason
    mainloop.quit()

c = pymsn.gnet.protocol.HTTP("www.google.com")
c.connect("response-received", response)
c.request("/")

mainloop.run()
