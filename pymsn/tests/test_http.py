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
    print resp.reason
    mainloop.quit()

c = gnet.protocol.HTTP("www.google.com")
c.connect("response-received", response)
c.request("/")

mainloop.run()
