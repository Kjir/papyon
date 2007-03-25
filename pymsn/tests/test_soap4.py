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
        self.abook.ABFindAll("Initial", self.contacts_cb)
        self.sharing.FindMembership("Initial", self.membership_cb)

    def membership_cb(self, soap_response, members):
        print members

    def contacts_cb(self, soap_response, contacts):
        for contact in contacts:
            print contact.account
            print contact.id
#         self.abook.ABContactUpdate(contacts[1].id,
#                                    {"displayName" : "Taratata",
#                                     "isMessengerUser" : "false"},
#                                    self.update1)
#         self.abook.ABContactUpdate(contacts[2].id,
#                                    { "isMessengerUser" : "false"},
#                                    self.update2)
        print "################################################"
        self.abook.ABContactUpdate("Timer", contacts[1].id,
                                   {"isMessengerUser" : "false"},
                                   self.update1)
#         self.abook.ABContactUpdate(contacts[4].id,{},self.update4)

    def update1(self, aa):
        print '1 done'

    def update2(self):
        print '2 done'

    def update3(self):
        print '3 done'

    def update4(self):
        print '4 done'

test = ABTests()
gobject.MainLoop().run()
