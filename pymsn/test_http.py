import gnet
import gnet.protocol
import gobject

mainloop = gobject.MainLoop()

def response(http, resp):
    global mainloop
    print resp.reason
    mainloop.quit()

c = gnet.protocol.HTTP("www.google.com")
c.connect("response-received", response)
c.request("/")

mainloop.run()
