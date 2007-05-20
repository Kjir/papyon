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
from base64 import b64encode
from string import join, split

__all__ = ['BaseRSI', 'BaseOIM']

NS_RSI = "http://www.hotmail.msn.com/ws/2004/09/oim/rsi"

class BaseRSI(object):

    def __init__(self, passport_security_token):
        self.__security_token = passport_security_token

    def _soap_action(self, method):
        return join([NS_RSI, method], '/')

    def _method_namespace(self, method):
        return NS_RSI

    def _soap_headers(self, method):
        """Needed headers for the current method"""
        PassportCookie = self.request.add_header("PassportCookie", NS_RSI)
        t,p = split(self.__security_token, ';')
        PassportCookie.append("t", value=t[2:len(t)])
        PassportCookie.append("p", value=p[2:len(t)])

NS_OIM = "http://messenger.msn.com/ws/2004/09/oim"
NS_RM = "http://schemas.xmlsoap.org/ws/2003/03/rm"
NS_UTILITY = "http://schemas.xmlsoap.org/ws/2002/07/utility"

class BaseOIM(object):

    def __init__(self, security_token):
        self.__security_token = security_token
        self._source_passport = ""
        self._fname = ""
        self._dest_passport = ""

        self._lock_key = None 
        
    def _soap_action(self, method):
        return join([NS_OIM, method], '/')

    def _method_namespace(self, method):
        return NS_OIM

    def _soap_headers(self, method):
        """Needed headers for the current method"""
        fname = "=?%s?%s?%s?=" % ("utf-8", "B", 
                                  b64encode(self._fname))
        attrib = { "memberName" : self._source_passport,
                   "friendlyName" : fname,
                   "xml:lang" : "nl-nl",
                   "proxy" : "MSNMSGR",
                   "msnpVer" : "MSNP13",
                   "buildVer" : "8.0.0328" }
        self.request.add_header("From", NS_OIM, attrib)
        attrib = { "memberName" : self._dest_passport }
        self.request.add_header("To", NS_OIM, attrib)
        attrib = { "passport" : self.__security_token,
                   "appid" : "",
                   "lockkey" : "" } # lots of work here with the lockkey
        self.request.add_header("Ticket", NS_OIM, attrib)
        Sequence = self.request.add_header("Sequence", NS_RM)
        Sequence.append("Identifier", NS_UTILITY,
                        value="http://messenger.msn.com")
        Sequence.append("MessageNumber", value="")



