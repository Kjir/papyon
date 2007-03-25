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

class Error(Exception):
    soap_utils = SOAPUtils(NS_SHORTHANDS)
    
    def __init__(self, error_xml_dump):
        pass

    def __str__(self):
        pass

class Group(object):
    def __init__(self, xml_node):
        soap_utils = SOAPUtils(NS_SHORTHANDS)

        self.id = soap_utils.find_ex(xml_node, "./ab:groupId").text
        group_info = soap_utils.find_ex(xml_node, "./ab:groupInfo") 
        
        self.type = soap_utils.find_ex(group_info, "./ab:groupType").text
        self.name = soap_utils.find_ex(group_info, "./ab:name").text
        
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

    def ABFindAll(self, scenario, deltas_only, callback, *callback_args):
        self.__scenario = scenario
        self._simple_method("ABFindAll", callback, callback_args,
                ("abId", "00000000-0000-0000-0000-000000000000"),
                ("abView", "Full"), # add lastChanges to make deltasOnly usable
                ("deltasOnly", SOAPUtils.bool_to_string(deltas_only)),
                ("dynamicItemView", "Gleam"))

    def ABContactAdd(self, scenario, passport, messenger, type, 
                     callback, *callback_args):
        """call the ABContactAdd SOAP action

           @param scenario : the scenario to use for the action
           @param passport : the passport address of the contact to add
           @param messenger : True is this is a messenger contact, else False
           @param type : "Regular" or "LivePending" or "LiveAccepted"
        """
        self.__scenario = scenario
        self._method("ABContactAdd", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        Contact = self.request.add_argument("contacts", NS_ADDRESSBOOK).\
            append("Contact", NS_ADDRESSBOOK)
        ContactInfo = Contact.append("contactInfo", NS_ADDRESSBOOK)
        ContactInfo.append("contactType", NS_ADDRESSBOOK, value=type)
        ContactInfo.append("passportName", NS_ADDRESSBOOK, value=passport)
        ContactInfo.append("isMessengerUser", NS_ADDRESSBOOK, value=SOAPUtils.bool_to_string(messenger))
        self._send_request()

    def ABContactDelete(self, scenario, contact_id, callback, *callback_args):
        self.__scenario = scenario
        self._method("ABContactDelete", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        Contact = self.request.add_argument("contacts", NS_ADDRESSBOOK).\
            append("Contact", NS_ADDRESSBOOK)
        Contact.append("contactId", NS_ADDRESSBOOK, value=contact_id)
        self._send_request()
    
    # properties is a dict which keys can be : displayName, isMessengerUser
    def ABContactUpdate(self, scenario, contact_id, properties, callback, *callback_args):
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
        self._send_request()

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

    def ABGroupDelete(self, scenario, group_guid, callback, *callback_args):
        self.__scenario = scenario
        self._method("ABGroupDelete", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        self.request.add_argument("groupFilter", NS_ADDRESSBOOK).\
            append("groupIds", NS_ADDRESSBOOK).\
            append("guid", NS_ADDRESSBOOK, value=group_guid)
        self._send_request()

    def ABGroupUpdate(self, scenario, group_guid, group_name,
                      callback, *callback_args):
        self.__scenario = scenario
        self._method("ABGroupUpdate", callback, callback_args, {})
        self.request.add_argument("abId", NS_ADDRESSBOOK, value="00000000-0000-0000-0000-000000000000")
        Group = self.request.add_argument("groups", NS_ADDRESSBOOK).\
            append("Group", NS_ADDRESSBOOK)
        Group.append("groupId", NS_ADDRESSBOOK, value=group_guid)
        Group.append("groupInfo", NS_ADDRESSBOOK).\
            append("name", NS_ADDRESSBOOK, value=group_name)
        Group.append("propertiesChanged", NS_ADDRESSBOOK, value="GroupName")
        self._send_request()

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
            path = "./ABFindAllResponse/ABFindAllResult/groups".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            groups =  soap_response.body.find(path)
            groups_result = []
            for group in groups:
                groups_result.append(Group(group))
            path = "./ABFindAllResponse/ABFindAllResult/contacts".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            contacts = soap_response.body.find(path)
            contacts_result = []
            for contact in contacts:
                contacts_result.append(Contact(contact))
            return (soap_response, groups_result, contacts_result)
        elif method == "ABContactAdd":
            return (soap_response,)
        elif method == "ABContactDelete":
            return (soap_response,)
        elif method == "ABContactUpdate":
            return (soap_response,)
        elif method == "ABGroupAdd":
            path = "./ABGroupAddResponse/ABGroupAddResult/guid".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            guid = soap_response.body.find(path)
            return (soap_response, guid.text)
        elif method == "ABGroupDelete":
            return (soap_response,)
        elif method == "ABGroupUpdate":
            return (soap_response,)
        else:
            return SOAPService._extract_response(self, method, soap_response)
