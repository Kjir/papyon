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

import base64
import struct

__all__ = ['SingleSignOn', 'LiveService']

SERVICE_URL = "https://login.live.com/RST.srf"

NS_PASSPORT = "http://schemas.microsoft.com/Passport/SoapServices/PPCRL"
NS_WS_SECEXT = "http://schemas.xmlsoap.org/ws/2003/06/secext"
NS_WS_TRUST = "http://schemas.xmlsoap.org/ws/2004/04/trust"
NS_WS_ADDRESSING = "http://schemas.xmlsoap.org/ws/2004/03/addressing"
NS_WS_POLICY = "http://schemas.xmlsoap.org/ws/2002/12/policy"
NS_WS_ISSUE = "http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue"

MSN_USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; IDCRL 4.100.313.1; IDCRL-cfg 4.0.5633.0; App MsnMsgr.Exe, 8.1.168.0, {7108E71A-9926-4FCB-BCC9-9A9D3F32E423})" 

class LiveService(object):
    CONTACTS = ("contacts.msn.com", "?fs=1&id=24000&kv=7&rn=93S9SWWw&tw=0&ver=2.1.6000.1")
    MESSENGER = ("messenger.live.com", "?id=507")
    MESSENGER_CLEAR = ("messengerclear.live.com", "MBI_KEY_OLD")
    MESSENGER_SECURE = ("messengersecure.live.com", "MBI_SSL")
    SPACES = ("spaces.live.com", "MBI")
    TB = ("http://Passport.NET/tb", None)
    VOICE = ("voice.messenger.msn.com", "?id=69264")


class SingleSignOn(SOAPService):
    def __init__(self, username, password):
        self.__credentials = (username, password)
        SOAPService.__init__(self, SERVICE_URL)
    
    def RequestMultipleSecurityTokens(self, *services):
        assert(len(services) > 0), "RequestMultipleSecurityTokens requires at least 1 service"
        self._method("RequestMultipleSecurityTokens", {"Id": "RSTS"})
        i = 0
        for service in services:
            self.__request_security_token(i, service)
            i += 1
        self._send_request()

    def _soap_action(self, method):
        return ""

    def _method_namespace(self, method):
        return NS_PASSPORT

    def _soap_headers(self, method):
        """Add the needed headers for the current method"""
        #assert(method == "RequestMultipleSecurityTokens")
        # http://www.microsoft.com/globaldev/reference/lcid-all.mspx
        request_params = self.__serialize_request_params({"lc":"1033"})
        AuthInfo = self.request.add_header("AuthInfo", NS_PASSPORT, Id="PPAuthInfo")
        AuthInfo.append("HostingApp", NS_PASSPORT, value="{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}")
        AuthInfo.append("BinaryVersion", NS_PASSPORT, value="4")
        AuthInfo.append("UIVersion", NS_PASSPORT, value="1")
        AuthInfo.append("Cookies", NS_PASSPORT)
        AuthInfo.append("RequestParams", NS_PASSPORT, value=request_params)

        SecurityHeader = self.request.add_header("Security", NS_WS_SECEXT)
        UsernameToken = SecurityHeader.append("UsernameToken", NS_WS_SECEXT, Id="user")
        UsernameToken.append("Username", NS_WS_SECEXT, value=self.__credentials[0])
        UsernameToken.append("Password", NS_WS_SECEXT, value=self.__credentials[1])
    
    def _http_headers(self, method):
        SOAPService._http_headers(self, method)
        self.http_headers['User-Agent'] = MSN_USER_AGENT
        self.http_headers['Accept'] = "text/*"

    def __serialize_request_params(self, params):
        s = struct.pack("<L", len(params))
        for key, value in params.items():
            key = key.encode("ascii")
            value = value.encode("ascii")
            s += struct.pack("<L", len(key)) + key
            s += struct.pack("<L", len(value)) + value
        return base64.b64encode(s)

    def __request_security_token(self, id, live_service):
        RST = self.request.add_argument("RequestSecurityToken", NS_WS_TRUST, Id=("RST%d" % id))
        RST.append("RequestType", NS_WS_TRUST, value=NS_WS_ISSUE)
        RST.append("AppliesTo", NS_WS_POLICY).\
                append("EndpointReference", NS_WS_ADDRESSING).\
                append("Address", NS_WS_ADDRESSING, value=live_service[0])
        if live_service[1] is not None:
            RST.append("PolicyReference", NS_WS_SECEXT, URI=live_service[1])
