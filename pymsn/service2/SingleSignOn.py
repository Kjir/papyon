# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

from SOAPService import *
from description.SingleSignOn.RequestMultipleSecurityTokens import LiveService

import pymsn.storage

__all__ = ['SingleSignOn', 'LiveService']

class SingleSignOn(SOAPService):
    def __init__(self, username, password, proxies=None):
        self.__credentials = (username, password)
        self.__storage = pymsn.storage.get_storage(username, "security-tokens")
        self.__response_tokens = []
        SOAPService.__init__(self, "SingleSignOn", proxies)

    def RequestMultipleSecurityTokens(self, callback, errback, *services):
        """Requests multiple security tokens from the single sign on service.
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param services: one or more L{LiveService}"""
        method = self._service.RequestMultipleSecurityTokens

        url = self._service.url

        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(*self.__credentials)
        soap_body = method.soap_body(*services)

        self._send_request(url, soap_header, soap_body, soap_action,
            callback, errback, http_headers)

    def _response_handler(self, transport, http_response):
        callback, errback = SOAPService._response_handler(self,
                transport, http_response)

    def _error_handler(self, transport, error):
        callback, errback = SOAPService._error_handler(self,
                transport, error)


if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging

    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)
    
    signal.signal(signal.SIGTERM,
            lambda *args: gobject.idle_add(mainloop.quit()))

    sso = SingleSignOn(account, password)
    sso.RequestMultipleSecurityTokens(None, None, 
            LiveService.MESSENGER,
            LiveService.CONTACTS)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
