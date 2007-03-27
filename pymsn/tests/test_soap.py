import pymsn.storage
import pymsn.service.SOAPService as SOAPService
import pymsn.service.SingleSignOn as SSO
import pymsn.service.AddressBook as AddressBook
import gobject
import logging

logging.basicConfig(level=logging.DEBUG)

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

proxies = get_proxies()

NS_TEMP = "urn:xmethods-Temperature"
class TemperatureService(SOAPService.SOAPService):
    def __init__(self, url):
        SOAPService.SOAPService.__init__(self, url)

    def _soap_action(self, method):
        return ""

    def _method_namespace(self, method):
        return NS_TEMP

#test = TemperatureService("http://services.xmethods.net/soap/servlet/rpcrouter")
#test.getTemp(("string", "zipcode", "10000"))

#print '------------------------------------------------'
def membership_cb(soap_response, members):
    print members

def contacts_cb(soap_response, contacts):
    for contact in contacts:
        print contact.account


def sso_cb1(sso, soap_response, *tokens):
    sso.RequestMultipleSecurityTokens(sso_cb2, (), SSO.LiveService.CONTACTS) # check the storage

def sso_cb2(soap_response, *tokens):
    print tokens
    for token in tokens:
        if token.service_address == SSO.LiveService.CONTACTS[0]:
            if 'http' in proxies:
                abook = AddressBook.AB(token, proxies['http'])
                sharing = AddressBook.Sharing(token, proxies['http'])
            else:
                abook = AddressBook.AB(token)
                sharing = AddressBook.Sharing(token)
            break
    abook.ABFindAll("Initial", True, contacts_cb)
    sharing.FindMembership("Initial", membership_cb)

if 'https' in proxies:
    sso = SSO.SingleSignOn("kimbix@hotmail.com", "linox45", proxies['https'])
else:
    sso = SSO.SingleSignOn("kimbix@hotmail.com", "linox45")

sso.RequestMultipleSecurityTokens(sso_cb1, (sso,), SSO.LiveService.CONTACTS)


gobject.MainLoop().run()
