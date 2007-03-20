import pymsn.gnet
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
    print resp.reason
    mainloop.quit()

proxies = get_proxies()
if 'https' in proxies:
    c = pymsn.gnet.protocol.HTTP("www.google.com", proxy=proxies['http'])
else:
    c = pymsn.gnet.protocol.HTTP("www.google.com")

c.connect("response-received", response)
c.request("/")

mainloop.run()
