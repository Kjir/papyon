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

def response(http, resp):
    global mainloop
    print resp
    mainloop.quit()

def request(http, req):
    print req

c = gnet.protocol.HTTPS("www.gmail.com")
c.connect("response-received", response)
c.connect("request-sent", request)
c.request("/")

mainloop.run()
