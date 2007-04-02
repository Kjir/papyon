# -*- coding: utf-8 -*-
#
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

__all__ = ['BaseStorage']

NS_STORAGE = "http://www.msn.com/webservices/storage/w10"

class BaseStorage(object):
    
    def __init__(self, storage_security_token):
        self.__security_token = storage_security_token

    def _soap_action(self, method):
        return join([NS_STORAGE, method], '/')

    def _method_namespace(self, method):
        return NS_STORAGE

    def _soap_headers(self, method):
        """Needed headers for the current method"""
        #TODO: add <CacheKey>
        # AffinityCacheHeader = self.request.add_header("AffinityCacheHeader", NS_STORAGE)
        # AffinityCacheHeader.append("CacheKey", value="")

        StorageApplicationHeader = self.request.add_header("StorageApplicationHeader", NS_STORAGE)
        StorageApplicationHeader.append("ApplicationID", value="Messenger Client 8.0")
        StorageApplicationHeader.append("Scenario", value=self.__scenario)

        StorageUserHeader = self.request.add_header("StorageUserHeader", NS_STORAGE)
        StorageUserHeader.append("Puid", value="0")
        StorageUserHeader.append("TicketToken", value=self.__security_token)
