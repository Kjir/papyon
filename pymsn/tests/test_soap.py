import pymsn.storage
import pymsn.service.SOAPService as SOAPService
import pymsn.service.SingleSignOn as SSO
import pymsn.service.AddressBook as AddressBook
import gobject
import logging

logging.basicConfig(level=logging.DEBUG)

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
        print contact.passport_name


def sso_cb1(sso, soap_response, *tokens):
    sso.RequestMultipleSecurityTokens(sso_cb2, (), SSO.LiveService.CONTACTS) # check the storage

def sso_cb2(soap_response, *tokens):
    print tokens
    for token in tokens:
        if token.service_address == SSO.LiveService.CONTACTS[0]:
            abook = AddressBook.AddressBook(token)
            sharing = AddressBook.Sharing(token)
            break
    abook.ABFindAll(contacts_cb)
    sharing.FindMembership(membership_cb)


sso = SSO.SingleSignOn("kimbix@hotmail.com", "linox45")
sso.RequestMultipleSecurityTokens(sso_cb1, (sso,), SSO.LiveService.CONTACTS)


gobject.MainLoop().run()
