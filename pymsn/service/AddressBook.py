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

from SOAPService import SOAPService

from xml.utils import iso8601

__all__ = ['AddressBook', 'Sharing']

AB_SERVICE_URL = "http://contacts.msn.com/abservice/abservice.asmx"
SHARING_SERVICE_URL = "http://contacts.msn.com/abservice/SharingService.asmx"
NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"


class Member(object):
    def __init__(self, xml_node):
        self.membership_id = xml_node.find("./{%s}MembershipId" % NS_ADDRESSBOOK).text
        self.type = xml_node.find("./{%s}Type" % NS_ADDRESSBOOK).text
        self.state = xml_node.find("./{%s}State" % NS_ADDRESSBOOK).text
        self.deleted = self._bool(xml_node.find("./{%s}Deleted" % NS_ADDRESSBOOK).text)
        self.last_changed = iso8601.parse(xml_node.find("./{%s}LastChanged" % NS_ADDRESSBOOK).text)

    def _bool(self, text): #FIXME: we need a helper class with all the conversion utilities
        if text.lower() == "false":
            return False
        return True

class PassportMember(Member):
    def __init__(self, xml_node):
        Member.__init__(self, xml_node)
        self.passport_name = xml_node.find("./{%s}PassportName" % NS_ADDRESSBOOK).text
        self.passport_hidden = self._bool(xml_node.find("./{%s}PassportName" % NS_ADDRESSBOOK).text)
        self.passport_id = xml_node.find("./{%s}PassportId" % NS_ADDRESSBOOK).text
        self.CID = xml_node.find("./{%s}CID" % NS_ADDRESSBOOK).text
        display_name = xml_node.find("./{%s}DisplayName" % NS_ADDRESSBOOK)
        if display_name is not None:
            self.display_name = display_name.text

class EmailMember(Member):
    def __init__(self, xml_node):
        Member.__init__(self, xml_node)
        self.email = xml_node.find("./{%s}Email" % NS_ADDRESSBOOK).text

class Contact(object):
    def __init__(self, xml_node):
        pass


class _BaseAddressBook(object):
    def __init__(self, contacts_security_token):
        self.__security_token = contacts_security_token

    def _soap_action(self, method):
        return "http://www.msn.com/webservices/AddressBook/" + method

    def _method_namespace(self, method):
        return NS_ADDRESSBOOK

    def _soap_headers(self, method):
        """Add the needed headers for the current method"""
        ABApplicationHeader = self.request.add_header("ABApplicationHeader", NS_ADDRESSBOOK)
        ABApplicationHeader.append("ApplicationId", NS_ADDRESSBOOK,
                value="996CDE1E-AA53-4477-B943-2BE802EA6166")
        ABApplicationHeader.append("IsMigration", NS_ADDRESSBOOK, value="false")
        ABApplicationHeader.append("PartnerScenario", NS_ADDRESSBOOK, value="Initial")
        #TODO: add <CacheKey>

        ABAuthHeader = self.request.add_header("ABAuthHeader", NS_ADDRESSBOOK)
        ABAuthHeader.append("ManagedGroupRequest", NS_ADDRESSBOOK, value="false")
        ABAuthHeader.append("TicketToken", NS_ADDRESSBOOK, value=self.__security_token.security_token)


class AddressBook(_BaseAddressBook, SOAPService):
    def __init__(self, contacts_security_token):
        _BaseAddressBook.__init__(self, contacts_security_token)
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
            for contact in contacts:

        else:
            return SOAPService._extract_response(self, method, soap_response)


class Sharing(_BaseAddressBook, SOAPService):
    def __init__(self, contacts_security_token):
        _BaseAddressBook.__init__(self, contacts_security_token)
        SOAPService.__init__(self, SHARING_SERVICE_URL)

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
                    type = member.find("./{%s}Type" % NS_ADDRESSBOOK).text
                    if type == "Passport":
                        member_instance = PassportMember(member)
                    elif type == "Email":
                        member_instance = EmailMember(member)
                    else:
                        raise NotImplementedError("Unknown member type, please fix")
                    result[role.text].append(member_instance)
            return (result,)
        else:
            return SOAPService._extract_response(self, method, soap_response)
