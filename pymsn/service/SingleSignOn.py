# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2006-2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

from SOAPService import SOAPService, SOAPUtils
import pymsn.storage

import base64
import struct
import Crypto.Util.randpool as randpool
from Crypto.Hash import HMAC, SHA
from Crypto.Cipher import DES3
from xml.utils import iso8601
import time

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

NS_SHORTHANDS = {
        "ps" : NS_PASSPORT,
        "xmlenc" : NS_XML_ENC,
        "wsse" : NS_WS_SECEXT,
        "wst" : NS_WS_TRUST,
        "wsa" : NS_WS_ADDRESSING,
        "wsp" : NS_WS_POLICY,
        "wsi" : NS_WS_ISSUE,
        "wsu" : NS_WS_UTILITY }

class LiveService(object):
    CONTACTS = ("contacts.msn.com", "?fs=1&id=24000&kv=7&rn=93S9SWWw&tw=0&ver=2.1.6000.1")
    MESSENGER = ("messenger.live.com", "?id=507")
    MESSENGER_CLEAR = ("messengerclear.live.com", "MBI_KEY_OLD")
    MESSENGER_SECURE = ("messengersecure.live.com", "MBI_SSL")
    SPACES = ("spaces.live.com", "MBI")
    TB = ("http://Passport.NET/tb", None)
    VOICE = ("voice.messenger.msn.com", "?id=69264")

class WinCrypt(object):
    CRYPT_MODE_CBC = 1
    CALC_3DES      = 0x6603
    CALC_SHA1      = 0x8004

class SecurityToken(object):
    def __init__(self):
        self.type = ""
        self.service_address = ""
        self.lifetime = [0, 0]
        self.security_token = ""
        self.proof_token = ""

    def is_expired(self):
        return time.time() + 60 >= self.lifetime[1] # add 1 minute

    def mbi_crypt(self, nonce):
        # Read key and generate two derived keys
        key1 = base64.b64decode(self.proof_token)
        key2 = self._derive_key(key1, "WS-SecureConversationSESSION KEY HASH")
        key3 = self._derive_key(key1, "WS-SecureConversationSESSION KEY ENCRYPTION")

        # Create a HMAC-SHA-1 hash of nonce using key2
        hash = HMAC.new(key2, nonce, SHA).digest()

        #
        # Encrypt nonce with DES3 using key3
        #

        # IV (Initialization Vector): 8 bytes of random data
        iv = randpool.RandomPool().get_bytes(8)
        obj = DES3.new(key3, DES3.MODE_CBC, iv)

        # XXX: win32's Crypt API seems to pad the input with 0x08 bytes
        # to align on 72/36/18/9 boundary
        ciph = obj.encrypt(nonce + "\x08\x08\x08\x08\x08\x08\x08\x08")

        blob = struct.pack("<LLLLLLL", 28, WinCrypt.CRYPT_MODE_CBC,
                WinCrypt.CALC_3DES, WinCrypt.CALC_SHA1, len(iv), len(hash),
                len(ciph))
        blob += iv + hash + ciph
        return base64.b64encode(blob)

    def _derive_key(self, key, magic):
        hash1 = HMAC.new(key, magic, SHA).digest()
        hash2 = HMAC.new(key, hash1 + magic, SHA).digest()

        hash3 = HMAC.new(key, hash1, SHA).digest()            
        hash4 = HMAC.new(key, hash3 + magic, SHA).digest()
        return hash2 + hash4[0:4]

    def __str__(self):
        return "<SecurityToken type=\"%s\" address=\"%s\" lifetime=\"%s\">" % \
                (self.type, self.service_address, str(self.lifetime))

    def __repr__(self):
        return "<SecurityToken type=\"%s\" address=\"%s\" lifetime=\"%s\">" % \
                (self.type, self.service_address, str(self.lifetime))

class SingleSignOn(SOAPService):
    def __init__(self, username, password, https_proxy=None):
        self.__credentials = (username, password)
        self.__storage = pymsn.storage.get_storage(username, "security_tokens")
        self.__response_tokens = []
        SOAPService.__init__(self, SERVICE_URL, https_proxy)

    def RequestMultipleSecurityTokens(self, callback, callback_args, *services):
        assert(len(services) > 0), "RequestMultipleSecurityTokens requires at least 1 service"

        self._method("RequestMultipleSecurityTokens", callback, callback_args,
                {"Id" : "RSTS"})
        services = list(services)

        for service in services: # filter already available tokens
            if service[0] in self.__storage:
                token = self.__storage[service[0]]
                if not token.is_expired():
                    services.remove(service)
                    self.__response_tokens.append(token)

        if len(services) == 0: # FIXME: do something cleaner
            method, callback, callback_args = self.request_queue.pop(0)
            if callback is not None:
                arguments = tuple(callback_args) + tuple(self.__response_tokens)
                self.__response_tokens = []
                callback(None, *arguments)
        else:
            if LiveService.TB not in services:
                services.insert(0, LiveService.TB)
            for i, service in enumerate(services):
                self.__request_security_token(i, service)
            self._send_request()

    def _extract_response(self, method, soap_response):
        if method == "RequestMultipleSecurityTokens":
            paths =("./wst:RequestSecurityTokenResponseCollection",
                    "./wst:TokenType",
                    "./wsp:AppliesTo/wsa:EndpointReference/wsa:Address",
                    "./wst:LifeTime/wsu:Created",
                    "./wst:LifeTime/wsu:Expires",
                    "./wst:RequestedSecurityToken/wsse:BinarySecurityToken",
                    "./wst:RequestedSecurityToken/xmlenc:EncryptedData/xmlenc:CipherData/xmlenc:CipherValue",
                    "./wst:RequestedProofToken/wst:BinarySecret")
            result = self.__response_tokens + [soap_response]
            soap_utils = SOAPUtils(NS_SHORTHANDS)

            responses = soap_utils.find_ex(soap_response.body, paths[0])
            for response in responses:
                token = SecurityToken()
                token.type = soap_utils.find_ex(response, paths[1]).text
                token.service_address = soap_utils.find_ex(response, paths[2]).text
                token.lifetime[0] = iso8601.parse(soap_utils.find_ex(response, paths[3]).text)
                token.lifetime[1] = iso8601.parse(soap_utils.find_ex(response, paths[4]).text)
                t = soap_utils.find_ex(response, paths[5])
                if t is not None:
                    token.security_token = t.text
                else:
                    token.security_token = soap_utils.find_ex(response, paths[6]).text
                proof_token = soap_utils.find_ex(response, paths[7])
                if proof_token is not None:
                    token.proof_token = proof_token.text
                self.__storage[token.service_address] = token
                result.append(token)
            self.__response_tokens = []
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
