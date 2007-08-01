# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from pymsn.service.SOAPUtils import XMLTYPE
from pymsn.service.SingleSignOn import *

__all__ = ['RSI']

class RSI(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "RSI", proxies)

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def GetMetadata(self, callback, errback):
        self.__soap_request(self._service.GetMetadata, (), 
                            callback, errback)

    def _HandleGetMetadataResponse(self, callback, errback, response, user_data):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def GetMessage(self, callback, errback, message_id, mark_as_read):
        self.__soap_request(self._service.GetMessage, 
                            (message_id, XMLTYPE.bool.encode(mark_as_read)) 
                            callback, errback)

    def _HandleGetMessageResponse(self, callback, errback, response, user_data):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def DeleteMessages(self, callback, errback, message_id):
        self.__soap_request(self._service.DeleteMessages, (message_id),
                            callback, errback)
    
    def _HandleDeleteMessagesResponse(self, callback, errback, response, user_data):
        pass

    def __soap_request(self, method, args, callback, errback):
        token = str(self._tokens[LiveService.MESSENGER_CLEAR])

        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(token)
        soap_body = method.soap_body(*args)
        
        method_name = method.__name__.rsplit(".", 1)[1]
        self._send_request(method_name, self._service.url, 
                           soap_header, soap_body, soap_action, 
                           callback, errback, http_headers)
        
