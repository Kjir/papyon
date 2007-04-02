# -*- coding: utf-8 -*-
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from pymsn.service.SOAPService import SOAPService, SOAPUtils, SOAPFault

RSI_SERVICE_URL = "https://rsi.hotmail.com/rsi/rsi.amx"
NS_RSI = "http://www.hotmail.msn.com/ws/2004/09/oim/rsi"

NS_SHORTHANDS = { "rsi" : NS_RSI }

class Message(Object):
    def __init__(self, xml_node):

class RSIError(SOAPFault):
    def __init__(self, xml_node):
        SOAPFault.__init__(self, xml_node)

class RSIService(BaseRSI, SOAPService):

    def __init__(self, passport_security_token):
        BaseRSI.__init__(self, passport_security_token)
        SOAPService.__init__(self, RSI_SERVICE_URL)

    def GetMetadata(self, callback, *callback_args):
        self._simple_method("GetMetadata", callback, callback_args)

    def GetMessage(self, msg_guid, mark_as_read,
                   callback, *callback_args):
        self._method("GetMessage", callback, callback_args, {})
        self.request.add_argument("messageId", NS_RSI, value=msg_guid)
        self.request.add_argument("alsoMarkAsRead", NS_RSI, value=SOAPUtils.\
                                      bool_to_string(mark_as_read))
        self._send_request()

    def DeleteMessages(self, msg_guid, callback, *callback_args):
        self._method("DeleteMessages", callback, callback_args, {})
        self.request.add_argument("messageIds", NS_RSI).\
            append("messageId", NS_RSI, value=msg_guid)
        self._send_request()

    def _extract_response(self, method, soap_response):
        path = "./%sResponse".replace("/", "/{%s}" % NS_STORAGE) % method
        if soap_response.body.find(path) is None: 
            raise RSIError(soap_response.body)

        if method == "GetMetadata":
            # TODO : process xml metadata
            return (soap_response,)
        elif method == "GetMessage":
            # TODO : process e-mail data
            return (soap_response,)
        elif method == "DeleteMessages":
            return (soap_response,)
        else:
            return SOAPService._extract_response(self, method, soap_response)

