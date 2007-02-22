# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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
from consts import NetworkID
from pymsn.service.SOAPService import SOAPService, SOAPUtils

from xml.utils import iso8601

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
        self.display_name = soap_utils.find_ex(contact_info, "./ab:displayName").text
        self.CID = soap_utils.find_ex(contact_info, "./ab:CID").text

class AB(BaseAddressBook, SOAPService):
    def __init__(self, contacts_security_token):
        BaseAddressBook.__init__(self, contacts_security_token)
        SOAPService.__init__(self, AB_SERVICE_URL)

    def ABFindAll(self, callback, *callback_args):
        self._simple_method("ABFindAll", callback, callback_args,
                ("abId", "00000000-0000-0000-0000-000000000000"),
                ("abView", "Full"),
                ("deltasOnly", "false"),
                ("dynamicItemView", "Gleam"))

    def _extract_response(self, method, soap_response):
        if method == "ABFindAll":
            path = "./ABFindAllResponse/ABFindAllResult/contacts".replace("/", "/{%s}" % NS_ADDRESSBOOK)
            contacts = soap_response.body.find(path)
            result = []
            for contact in contacts:
                result.append(Contact(contact))
            return (soap_response, result)
        else:
            return SOAPService._extract_response(self, method, soap_response)

