# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
from pymsn.service.SOAPService import SOAPService, SOAPUtils, SOAPFault

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
            self.network_id = NetworkID.MSN
        else:
            self.account = soap_utils.find_ex(xml_node, "./ab:Email").text
            self.network_id = NetworkID.EXTERNAL

        display_name = soap_utils.find_ex(xml_node, "./ab:DisplayName")
        if display_name is not None:
            self.display_name = display_name.text
        else:
            self.display_name = self.account.split("@", 1)[0]

class SharingError(SOAPFault):
    def __init__(self, xml_node):
        SOAPFault.__init__(self, xml_node)

class Sharing(BaseAddressBook, SOAPService):
    def __init__(self, contacts_security_token, http_proxy=None):
        BaseAddressBook.__init__(self, contacts_security_token)
        SOAPService.__init__(self, SHARING_SERVICE_URL, http_proxy)

    def FindMembership(self, scenario, callback, *callback_args):
        self._scenario = scenario
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

    def AddMember(self, scenario, passport, member_role,
                  callback, *callback_args):
        self._scenario = scenario
        self._method("AddMember", callback, callback_args, {})
        serviceHandle = self.request.add_argument("serviceHandle", NS_ADDRESSBOOK)
        serviceHandle.append("Id", NS_ADDRESSBOOK, value="0")
        serviceHandle.append("Type", NS_ADDRESSBOOK, value="Messenger")
        serviceHandle.append("ForeignId", NS_ADDRESSBOOK, value="")
        Membership = self.request.add_argument("memberships", NS_ADDRESSBOOK).\
            append("Membership", NS_ADDRESSBOOK)
        Membership.append("MemberRole", NS_ADDRESSBOOK, value=member_role)
        Member = Membership.append("Members", NS_ADDRESSBOOK).\
                append("Member", NS_ADDRESSBOOK, #FIXME: ugly ugly hack
                    attrib={"xsi:type": "ns1:PassportMember", "xmlns:xsi" : "http://www.w3.org/2001/XMLSchema-instance"})
        Member.append("Type", NS_ADDRESSBOOK, value="Passport")
        Member.append("State", NS_ADDRESSBOOK, value="Accepted")
        Member.append("PassportName", NS_ADDRESSBOOK, value=passport)
        self._send_request()

    def DeleteMember(self, scenario, member_role, member_id, passport,
                     callback, *callback_args):
        self._scenario = scenario
        self._method("DeleteMember", callback, callback_args, {})
        serviceHandle = self.request.add_argument("serviceHandle", NS_ADDRESSBOOK)
        serviceHandle.append("Id", NS_ADDRESSBOOK, value="0")
        serviceHandle.append("Type", NS_ADDRESSBOOK, value="Messenger")
        serviceHandle.append("ForeignId", NS_ADDRESSBOOK, value="")
        Membership = self.request.add_argument("memberships", NS_ADDRESSBOOK).\
            append("Membership", NS_ADDRESSBOOK)
        Membership.append("MemberRole", NS_ADDRESSBOOK, value=member_role)
        Member = Membership.append("Members", NS_ADDRESSBOOK).\
                append("Member", NS_ADDRESSBOOK, #FIXME: ugly ugly hack
                    attrib={"xsi:type": "ns1:PassportMember", "xmlns:xsi" : "http://www.w3.org/2001/XMLSchema-instance"})
        Member.append("Type", NS_ADDRESSBOOK, value="Passport")
        #Member.append("MembershipId", NS_ADDRESSBOOK, value=member_id)
        Member.append("State", NS_ADDRESSBOOK, value="Accepted")
        Member.append("PassportName", NS_ADDRESSBOOK, value=passport)
        self._send_request()

    def _extract_response(self, method, soap_response):
        path = "./%sResponse".replace("/", "/{%s}" % NS_ADDRESSBOOK) % method
        if soap_response.body.find(path) is None: 
            raise SharingError(soap_response.body)

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
        elif method == "AddMember":
            pass
        elif method == "DeleteMember":
            pass
        else:
            return SOAPService._extract_response(self, method, soap_response)
