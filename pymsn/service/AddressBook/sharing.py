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

__all__ = ['Sharing']

SHARING_SERVICE_URL = "http://contacts.msn.com/abservice/SharingService.asmx"
NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"

NS_SHORTHANDS = {"ab": NS_ADDRESSBOOK}


class Member(object):
    def __init__(self, xml_node):
        soap_utils = SOAPUtils(NS_SHORTHANDS)

        self.membership_id = soap_utils.find_ex(xml_node, "./ab:MembershipId").text
        self.type = soap_utils.find_ex(xml_node, "./ab:Type").text
        self.state = soap_utils.find_ex(xml_node, "./ab:State").text
        self.deleted = SOAPUtils.bool_type(soap_utils.find_ex(xml_node, "./ab:Deleted").text)
        self.last_changed = iso8601.parse(soap_utils.find_ex(xml_node, "./ab:LastChanged").text)
        
        passport = soap_utils.find_ex(xml_node, "./ab:PassportName")
        if passport is not None:
            self.account = passport.text
            self.netword_id = NetworkID.MSN
        else:
            self.account = soap_utils.find_ex(xml_node, "./ab:Email").text
            self.netword_id = NetworkID.EXTERNAL

        display_name = soap_utils.find_ex(xml_node, "./ab:DisplayName")
        if display_name is not None:
            self.display_name = display_name.text
        else:
            self.display_name = self.account.split("@", 1)[0]

class Sharing(BaseAddressBook, SOAPService):
    def __init__(self, contacts_security_token):
        BaseAddressBook.__init__(self, contacts_security_token)
        SOAPService.__init__(self, SHARING_SERVICE_URL)

    def _soap_headers(self, method):
        if method == "FindMemberShip":
            BaseAddressBook._soap_headers(self, method, "Initial")
        else:
            # We guess Timer to be the default scenario
            BaseAddressBook._soap_headers(self, method, "Timer")

    def FindMembership(self, callback, *callback_args):
        self._method("FindMembership", callback, callback_args, {})
        ServiceType = self.request.add_argument("serviceFilter", NS_ADDRESSBOOK).\
            append("Types", NS_ADDRESSBOOK)
        ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="Messenger")
        ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="Invitation")
        #ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="SocialNetwork")
        #ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="Space")
        #ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="Profile")
        #if last_change is not None:
        #    self.request.add_argument("View", NS_ADDRESSBOOK, value="Full")
        #    self.request.add_argument("deltasOnly", NS_ADDRESSBOOK, value="true")
        #    self.request.add_argument("lastChange", NS_ADDRESSBOOK, value=last_change)
        self._send_request()

    def _extract_response(self, method, soap_response):
        if method == "FindMembership":
            path = "./FindMembershipResponse/FindMembershipResult/Services/Service/Memberships".\
                    replace("/", "/{%s}" % NS_ADDRESSBOOK)
            memberships = soap_response.body.find(path)
            result = {}
            for membership in memberships:
                role = membership.find("./{%s}MemberRole" % NS_ADDRESSBOOK)
                members = membership.find("./{%s}Members" % NS_ADDRESSBOOK)
                if role is None or members is None:
                    continue
                result[role.text] = []
                for member in members:
                    result[role.text].append(Member(member))
            return (soap_response, result)
        else:
            return SOAPService._extract_response(self, method, soap_response)
