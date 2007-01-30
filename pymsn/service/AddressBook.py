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

#FIXME: not quite sure about this :/
#FIXME: really ugly, I hate this
import sys, os
parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir) 
del parent_dir
del sys
del os

from service.SOAPService import SOAPService


__all__ = ['AddressBook']

SERVICE_URL = "http://contacts.msn.com/abservice/SharingService.asmx"
NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"

class AddressBook(SOAPService):
    def __init__(self, username, password):
        self.__credentials = (username, password)
        SOAPService.__init__(self, SERVICE_URL)
    
    def FindMembership(self, callback, callback_args):
        self._method("FindMembership", callback, callback_args)
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

        ABAuthHeader = self.request.add_header("ABAuthHeader", NS_ADDRESSBOOK)
        ABAuthHeader.append("ManagedGroupRequest", NS_ADDRESSBOOK, value="false")
    
    def _http_headers(self, method):
        SOAPService._http_headers(self, method)
        #self.http_headers['User-Agent'] = MSN_USER_AGENT
        self.http_headers['Accept'] = "text/*"
