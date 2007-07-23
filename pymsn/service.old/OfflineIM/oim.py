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

from base import BaseOIM
from pymsn.service.SOAPService import SOAPService, SOAPUtils

OIM_SERVICE_URL = "https://ows.messenger.msn.com/OimWS/oim.asmx"
NS_OIM = "http://messenger.msn.com/ws/2004/09/oim"

NS_SHORTHANDS = { "oim" : NS_OIM }

class OIMService(BaseOIM, SOAPService):

    def __init__(self, passport_security_token, http_proxy=None):
        BaseOIM.__init__(self, passport_security_token)
        SOAPService.__init__(self, OIM_SERVICE_URL, http_proxy)

    def Store(self, source_passport, fname, recipient_passport,
              sequence_number, callback, *callback_args):
        self._source_passport = source_passport
        self._fname = fname
        self._recipient_passport = recipient_passport
        self._sequence_number = sequence_number
        if True: raise NotImplementedError

    def _extract_response(self, method, soap_response):
        #path = "./%sResponse".replace("/", "/{%s}" % NS_STORAGE) % method

        if method == "Store":
            return (soap_reponse,)
        else:
            return SOAPService._extract_response(self, method, soap_response)

