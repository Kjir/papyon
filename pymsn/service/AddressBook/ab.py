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
from pymsn.service.SOAPService import SOAPService

from xml.utils import iso8601

__all__ = ['AB']

AB_SERVICE_URL = "http://contacts.msn.com/abservice/abservice.asmx"
NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"

class Contact(object):
    def __init__(self, xml_node):
        self.contact_id = xml_node.find("./{%s}contactId" % NS_ADDRESSBOOK).text
        contact_info = xml_node.find("./{%s}contactInfo" % NS_ADDRESSBOOK)
        self.contact_type = contact_info.find("./{%s}contactType" % NS_ADDRESSBOOK).text
        self.passport_name = contact_info.find("./{%s}passportName" % NS_ADDRESSBOOK).text
        self.passport_hidden = self._bool(contact_info.find("./{%s}IsPassportNameHidden" % NS_ADDRESSBOOK).text)
        self.display_name = contact_info.find("./{%s}displayName" % NS_ADDRESSBOOK).text
        self.CID = contact_info.find("./{%s}CID" % NS_ADDRESSBOOK).text

    def _bool(self, text): #FIXME: we need a helper class with all the conversion utilities
        if text.lower() == "false":
            return False
        return True


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

