import gnet
import gnet.protocol
import gobject

mainloop = gobject.MainLoop()

def response(http, resp):
    global mainloop
    print resp
    mainloop.quit()

c = gnet.protocol.HTTPS("www.gmail.com")
c.connect("response-received", response)
c.request("/")

mainloop.run()
