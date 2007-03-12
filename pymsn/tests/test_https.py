import pymsn.gnet.protocol
import gobject

mainloop = gobject.MainLoop()

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

def response(http, resp):
    global mainloop
    print resp
    mainloop.quit()

def request(http, req):
    print req

uagent = "Mozilla/4.0"
proxies = get_proxies()
if 'https' in proxies:
    c = pymsn.gnet.protocol.HTTPS("www.rtai.org", proxy=proxies['https'])
else:
    c = pymsn.gnet.protocol.HTTPS("www.rtai.org")

c.connect("response-received", response)
c.connect("request-sent", request)
c.request("/")

mainloop.run()
