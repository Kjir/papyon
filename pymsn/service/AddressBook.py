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

__all__ = ['AddressBook']

AB_SERVICE_URL = "http://contacts.msn.com/abservice/abservice.asmx"
SHARING_SERVICE_URL = "http://contacts.msn.com/abservice/SharingService.asmx"
NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"


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
        ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="SocialNetwork")
        ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="Space")
        ServiceType.append("ServiceType", NS_ADDRESSBOOK, value="Profile")
        #if last_change is not None:
        #    self.request.add_argument("View", NS_ADDRESSBOOK, value="Full")
        #    self.request.add_argument("deltasOnly", NS_ADDRESSBOOK, value="true")
        #    self.request.add_argument("lastChange", NS_ADDRESSBOOK, value=last_change)
        self._send_request()
