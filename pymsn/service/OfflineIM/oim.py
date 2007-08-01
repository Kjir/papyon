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

from pymsn.msnp.notification import ProtocolConstant
from pymsn.service.SingleSignOn import *

__all__ = ['OIM']

class OIM(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        self.__lock_key = ""
        SOAPService.__init__(self, "OIM", proxies)

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def Store(self, callback, errback, from_member_name, friendly_name, 
              to_member_name, message_number, message_type, message_content):
        token = str(self._tokens[LiveService.MESSENGER_CLEAR])
        fname = "=?utf-8?B?%s=" % friendly_name.encode('base64')

        # TODO : encode message_content in the right mail format
        content = message_content 

        self.__soap_request(self._service.Store,
                            (from_member_name, fname, 
                             ProtocolConstant.CVR[4],
                             ProtocolConstant.VER[2],
                             ProtocolConstant.CVR[5],
                             to_member_name,
                             message_number, 
                             token,
                             ProtocolConstant.PRODUCT_ID,
                             self.__lock_key),
                            (message_type, content),
                            callback, errback)
    
    def _HandleStoreResponse(self, callback, errback, response, user_data):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def Store2(self, callback, errback, from_member_name, friendly_name, 
               to_member_name, message_number, message_type, message_content):
        token = str(self._tokens[LiveService.MESSENGER_CLEAR])
        fname = "=?utf-8?B?%s=" % friendly_name.encode('base64')

        # TODO : encode message_content in the right mail format
        content = message_content 

        self.__soap_request(self._service.Store2,
                            (from_member_name, fname, 
                             ProtocolConstant.CVR[4],
                             ProtocolConstant.VER[2],
                             ProtocolConstant.CVR[5],
                             to_member_name,
                             message_number, 
                             token,
                             ProtocolConstant.PRODUCT_ID,
                             self.__lock_key),
                            (message_type, content),
                            callback, errback)

    def _HandleStore2Response(self, callback, errback, response, user_data):
        pass
    
    def __soap_request(self, method, header_args, body_args, 
                       callback, errback):
        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(*header_args)
        soap_body = method.soap_body(*body_args)
        
        method_name = method.__name__.rsplit(".", 1)[1]
        self._send_request(method_name, self._service.url, 
                           soap_header, soap_body, soap_action, 
                           callback, errback, http_headers)
