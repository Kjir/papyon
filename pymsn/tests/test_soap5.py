import pymsn.storage
import pymsn.service.SOAPService as SOAPService
import pymsn.service.SingleSignOn as SSO
import pymsn.service.AddressBook as AddressBook
import gobject
import logging

logging.basicConfig(level=logging.DEBUG)

class ABTests:

    def __init__(self):
        self.abook = None
        self.sharing = None
        sso = SSO.SingleSignOn("im_a_jabber_monkey@hotmail.com", "pymsn_1s_great")
        sso.RequestMultipleSecurityTokens(self.sso_cb1, (sso,), SSO.LiveService.CONTACTS)

    def sso_cb1(self, sso, soap_response, *tokens):
        sso.RequestMultipleSecurityTokens(self.sso_cb2, (), SSO.LiveService.CONTACTS) # check the storage

    def sso_cb2(self, soap_response, *tokens):
        print tokens
        for token in tokens:
            if token.service_address == SSO.LiveService.CONTACTS[0]:
                self.abook = AddressBook.AB(token)
                self.sharing = AddressBook.Sharing(token)
                break
        self.abook.ABFindAll("Initial", False, self.contacts_cb)
        self.sharing.FindMembership("Initial", self.membership_cb)

    def membership_cb(self, soap_response, members):
        print members

    def contacts_cb(self, soap_response, contacts):
        for contact in contacts:
            print contact.account
            print contact.id
        self.abook.ABContactAdd("ContactSave", 
                                "johann.prieur@gmail.com",
                                True,
                                "LivePending",
                                self.contact_add_cb)
        
    def contact_add_cb(self, soap_response, guid):
        print "The guid for the added contact is " + guid
        self.abook.ABFindAll("ContactSave", True, self.findall)

    def findall(self, soap_response, contacts):
        for contact in contacts:
            print contact.account
            print contact.id

test = ABTests()
gobject.MainLoop().run()
