# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from base import BaseAddressBook
from pymsn.profile import NetworkID
from pymsn.service.SOAPService import SOAPService, SOAPUtils

from xml.utils import iso8601
from string import upper, join

__all__ = ['AB']

AB_SERVICE_URL = "http://contacts.msn.com/abservice/abservice.asmx"
NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"

NS_SHORTHANDS = {"ab": NS_ADDRESSBOOK}

class Contact(object):
    def __init__(self, xml_node):
        soap_utils = SOAPUtils(NS_SHORTHANDS)

        self.id = soap_utils.find_ex(xml_node, "./ab:contactId").text
        contact_info = soap_utils.find_ex(xml_node, "./ab:contactInfo")

        self.type = soap_utils.find_ex(contact_info, "./ab:contactType").text

        passport = soap_utils.find_ex(contact_info, "./ab:passportName")
        if passport is not None:
            self.account = passport.text
            self.netword_id = NetworkID.MSN
        else: # Yahoo user
            self.account = soap_utils.find_ex(contact_info,
                    "./ab:emails/ab:ContactEmail/ab:email").text
            self.netword_id = NetworkID.EXTERNAL
        display_name = soap_utils.find_ex(xml_node, "./ab:DisplayName")
        if display_name is not None:
            self.display_name = display_name.text
        else:
            self.display_name = self.account.split("@", 1)[0]
        self.CID = soap_utils.find_ex(contact_info, "./ab:CID").text


class AB(BaseAddressBook, SOAPService):
    def __init__(self, contacts_security_token, http_proxy=None):
        BaseAddressBook.__init__(self, contacts_security_token)
        SOAPService.__init__(self, AB_SERVICE_URL, http_proxy)

#     def _soap_headers(self, method):
#         if method == "ABFindAll":
#             BaseAddressBook._soap_headers(self, method, "Initial")
#         elif method == "ABContactAdd":
#             BaseAddressBook._soap_headers(self, method, "ContactSave")
#         elif method == "ABContactDelete":
#             BaseAddressBook._soap_headers(self, method, "Timer")
#         elif method == "ABContactUpdate":
#             BaseAddressBook._soap_headers(self, method, "Timer")
#         elif method == "ABGroupAdd":
#             BaseAddressBook._soap_headers(self, method, "GroupSave")
#         elif method == "ABGroupDelete":
#             BaseAddressBook._soap_headers(self, method, "Timer")
#         elif method == "ABGroupUpdate":
#             BaseAddressBook._soap_headers(self, method, "GroupSave")
#         elif method == "ABGroupContactAdd":
#             BaseAddressBook._soap_headers(self, method, "GroupSave")
#         elif method == "ABGroupContactDelete":
#             BaseAddressBook._soap_headers(self, method, "GroupSave")
#         elif method == "UpdateDynamicItem":
#             BaseAddressBook._soap_headers(self, method, "RoamingIdentityChanged")
#         else:
#             # We guess Timer to be the default scenario
#             BaseAddressBook._soap_headers(self, method, "Timer")

    def ABFindAll(self, scenario, callback, *callback_args):
        self.__scenario = scenario
        self._simple_method("ABFindAll", callback, callback_args,
                ("abId", "00000000-0000-0000-0000-000000000000"),
                ("abView", "Full"),
                ("deltasOnly", "false"),
                ("dynamicItemView", "Gleam"))

    def ABContactAdd(self, scenario, properties, callback, *callback_args):
        self.__scenario = scenario
        self._method("ABContactAdd", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        Contact = self.request.add_argument("contacts", NS_ADDRESSBOOK).\
            append("Contact", NS_ADDRESSBOOK)
        ContactInfo = Contact.append("contactInfo", NS_ADDRESSBOOK)
        for property, nvalue in properties.iteritems():
            if nvalue is None: break
            ContactInfo.append(property, NS_ADDRESSBOOK, value=nvalue)
        # TODO : add MessengerMemberInfo?
        self._send_request()

    def ABContactDelete(self, scenario, contact_id, callback, *callback_args):
        self.__scenario = scenario
        self._method("ABContactDelete", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        Contact = self.request.add_argument("contacts", NS_ADDRESSBOOK).\
            append("Contact", NS_ADDRESSBOOK)
        Contact.append("contactId", NS_ADDRESSBOOK, value=contact_id)
        self._send_request()
    
    # properties is a dict which keys can be : displayName, isMessengerUser... boolean values
    def ABContactUpdate(self, scenario, contact_id, properties, callback, *callback_args):
        print "£££££££££££££££££££££££££££££££££££££££££££££££"
        self.__scenario = scenario
        self._method("ABContactUpdate", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        Contact = self.request.add_argument("contacts", NS_ADDRESSBOOK).\
            append("Contact", NS_ADDRESSBOOK)
        Contact.append("contactId", NS_ADDRESSBOOK, value=contact_id)
        ContactInfo = Contact.append("contactInfo", NS_ADDRESSBOOK)
        # TODO : add ContactType?
        changed = []
        for property, nvalue in properties.iteritems():
            if nvalue is None: break
            ContactInfo.append(property, NS_ADDRESSBOOK, value=nvalue)
            changed.append(upper(property[0]) + property[1:len(property)])
        Contact.append("propertiesChanged", NS_ADDRESSBOOK, value=join(changed))
        print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"
        self._send_request()
        print "€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€"

    def ABGroupAdd(self, scenario, group_name, callback, *callback_args):
        self.__scenario = scenario
        self._method("ABGroupAdd", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        GroupAddOptions = self.request.add_argument("groupAddOptions", NS_ADDRESSBOOK)
        GroupAddOptions.append("fRenameOnMsgrConflict", NS_ADDRESSBOOK, value="false")
        GroupInfo = self.request.add_argument("groupInfo", NS_ADDRESSBOOK).\
            append("GroupInfo", NS_ADDRESSBOOK)
        GroupInfo.append("name", NS_ADDRESSBOOK, value=group_name)
        GroupInfo.append("groupType", NS_ADDRESSBOOK, value="C8529CE2-6EAD-434d-881F-341E17DB3FF8")
        GroupInfo.append("fMessenger", NS_ADDRESSBOOK, value="false")
        Annotation = GroupInfo.append("annotations", NS_ADDRESSBOOK).\
            append("Annotation", NS_ADDRESSBOOK)
        Annotation.append("Name", NS_ADDRESSBOOK, value="MSN.IM.DISPLAY")
        Annotation.append("Value", NS_ADDRESSBOOK, value="1")
        self._send_request()

    def ABGroupDelete(self, scenario, callback, *callback_args):
        self.__scenario = scenario
        pass

    def ABGroupUpdate(self, scenario, callback, *callback_args):
        self.__scenario = scenario
        pass

    def ABGroupContactAdd(self, scenario, callback, *callback_args):
        self.__scenario = scenario
        pass

    def ABGroupContactDelete(self, scenario, callback, *callback_args):
        self.__scenario = scenario
        pass

    def UpdateDynamicItem(self, scenario, callback, *callback_args):
        self.__scenario = scenario
        pass
    

    def _extract_response(self, method, soap_response):
        if method == "ABFindAll":
            path = "./ABFindAllResponse/ABFindAllResult/contacts".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            contacts = soap_response.body.find(path)
            result = []
            for contact in contacts:
                result.append(Contact(contact))
            return (soap_response, result)
        elif method == "ABContactAdd":
            path = "./ABContactAddResponse/ABContactAddResult/guid".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            guid = soap_response.body.find(path)
            return (soap_response, guid.text)
        elif method == "ABContactDelete":
            return (soap_response,)
        elif method == "ABContactUpdate":
            return (soap_response,)
        elif method == "ABGroupAdd":
            path = "./ABGroupAddResponse/ABGroupAddResult/guid".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            guid = soap_response.body.find(path)
            return (soap_response, guid.text)
        else:
            return SOAPService._extract_response(self, method, soap_response)
