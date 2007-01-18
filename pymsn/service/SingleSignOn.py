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
from xml.utils import iso8601

__all__ = ['SingleSignOn', 'LiveService']

SERVICE_URL = "https://login.live.com/RST.srf"

NS_PASSPORT = "http://schemas.microsoft.com/Passport/SoapServices/PPCRL"
NS_XML_ENC = "http://www.w3.org/2001/04/xmlenc#"
NS_WS_SECEXT = "http://schemas.xmlsoap.org/ws/2003/06/secext"
NS_WS_TRUST = "http://schemas.xmlsoap.org/ws/2004/04/trust"
NS_WS_ADDRESSING = "http://schemas.xmlsoap.org/ws/2004/03/addressing"
NS_WS_POLICY = "http://schemas.xmlsoap.org/ws/2002/12/policy"
NS_WS_ISSUE = "http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue"
NS_WS_UTILITY = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"

MSN_USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; IDCRL 4.100.313.1; IDCRL-cfg 4.0.5633.0; App MsnMsgr.Exe, 8.1.168.0, {7108E71A-9926-4FCB-BCC9-9A9D3F32E423})" 

class LiveService(object):
    CONTACTS = ("contacts.msn.com", "?fs=1&id=24000&kv=7&rn=93S9SWWw&tw=0&ver=2.1.6000.1")
    MESSENGER = ("messenger.live.com", "?id=507")
    MESSENGER_CLEAR = ("messengerclear.live.com", "MBI_KEY_OLD")
    MESSENGER_SECURE = ("messengersecure.live.com", "MBI_SSL")
    SPACES = ("spaces.live.com", "MBI")
    TB = ("http://Passport.NET/tb", None)
    VOICE = ("voice.messenger.msn.com", "?id=69264")


class SecurityToken(object):
    def __init__(self):
        self.type = ""
        self.service_address = ""
        self.lifetime = [0, 0]
        self.security_token = ""
        self.proof_token = ""

    def __str__(self):
        return "<SecurityToken type=\"%s\" address=\"%s\" lifetime=\"%s\">" % \
                (self.type, self.service_address, str(self.lifetime))

    def __repr__(self):
        return "<SecurityToken type=\"%s\" address=\"%s\" lifetime=\"%s\">" % \
                (self.type, self.service_address, str(self.lifetime))


class SingleSignOn(SOAPService):
    def __init__(self, username, password):
        self.__credentials = (username, password)
        SOAPService.__init__(self, SERVICE_URL)
    
    def RequestMultipleSecurityTokens(self, callback, *services):
        assert(len(services) > 0), "RequestMultipleSecurityTokens requires at least 1 service"
        self._method("RequestMultipleSecurityTokens", callback, {"Id": "RSTS"})
        i = 0
        for service in services:
            self.__request_security_token(i, service)
            i += 1
        self._send_request()

    def _extract_response(self, method, soap_response):
        if method == "RequestMultipleSecurityTokens":
            paths =("./{%s}RequestSecurityTokenResponseCollection" % NS_WS_TRUST,
                    "./{%s}TokenType" % NS_WS_TRUST,
                    "./{%s}AppliesTo/{%s}EndpointReference/{%s}Address" %
                            (NS_WS_POLICY, NS_WS_ADDRESSING, NS_WS_ADDRESSING),
                    "./{%s}LifeTime/{%s}Created" % (NS_WS_TRUST, NS_WS_UTILITY),
                    "./{%s}LifeTime/{%s}Expires" % (NS_WS_TRUST, NS_WS_UTILITY),
                    "./{%s}RequestedSecurityToken/{%s}BinarySecurityToken" %
                            (NS_WS_TRUST, NS_WS_SECEXT),
                    "./{%s}RequestedSecurityToken/{%s}EncryptedData/{%s}CipherData/{%s}CipherValue" %
                            (NS_WS_TRUST, NS_XML_ENC, NS_XML_ENC, NS_XML_ENC),
                    "./{%s}RequestedProofToken/{%s}BinarySecret" %
                            (NS_WS_TRUST, NS_WS_TRUST))
            result = [soap_response]
            responses = soap_response.body.find(paths[0])
            for response in responses:
                token = SecurityToken()
                token.type = response.find(paths[1]).text
                token.service_address = response.find(paths[2]).text
                token.lifetime[0] = iso8601.parse(response.find(paths[3]).text)
                token.lifetime[1] = iso8601.parse(response.find(paths[4]).text)
                t = response.find(paths[5])
                if t is not None:
                    token.security_token = t.text
                else:
                    token.security_token = response.find(paths[6]).text
                token.proof_token = response.find(paths[7]).text
                result.append(token)
            return result
        else:
            return SOAPService._extract_response(self, method, soap_response)

    def _soap_action(self, method):
        return ""

    def _method_namespace(self, method):
        return NS_PASSPORT

    def _soap_headers(self, method):
        """Add the needed headers for the current method"""
        assert(method == "RequestMultipleSecurityTokens")
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
