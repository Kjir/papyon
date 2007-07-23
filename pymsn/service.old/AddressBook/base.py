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

from pymsn.service.SOAPService import SOAPService

from xml.utils import iso8601
from string import join

__all__ = ['BaseAddressBook']

NS_ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"

class BaseAddressBook(object):
    def __init__(self, contacts_security_token):
        self._security_token = contacts_security_token
        self._scenario = None

    def _soap_action(self, method):
        return join([NS_ADDRESSBOOK, method], '/')

    def _method_namespace(self, method):
        return NS_ADDRESSBOOK

    def _soap_headers(self, method):
        """Add the needed headers for the current method"""
        ABApplicationHeader = self.request.add_header("ABApplicationHeader", NS_ADDRESSBOOK)
        ABApplicationHeader.append("ApplicationId", NS_ADDRESSBOOK,
                value="996CDE1E-AA53-4477-B943-2BE802EA6166") 
        ABApplicationHeader.append("IsMigration", NS_ADDRESSBOOK, value="false")
        ABApplicationHeader.append("PartnerScenario", NS_ADDRESSBOOK, value=self._scenario)
        #TODO: add <CacheKey>

        ABAuthHeader = self.request.add_header("ABAuthHeader", NS_ADDRESSBOOK)
        ABAuthHeader.append("ManagedGroupRequest", NS_ADDRESSBOOK, value="false")
        ABAuthHeader.append("TicketToken", NS_ADDRESSBOOK, value=self._security_token.security_token)
