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

from pymsn.service.SOAPService import SOAPService
from pymsn.service.SOAPUtils import XMLTYPE
from pymsn.service.SingleSignOn import *

__all__ = ['Storage']

class Storage(SOAPService):

    # FIXME : find which security token is used with that service

    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "SchematizedStore", proxies)

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def GetProfile(self, callback, errback, scenario, cid, profile_rid, 
                   p_date_modified, expression_rid, e_date_modified, 
                   display_name, dn_last_modified, personal_status, 
                   ps_last_modified, user_tile_url, photo, flags):
        self.__soap_request(self._service.GetProfile, scenario,
                 (cid, 
                  XMLTYPE.bool.encode(profile_rid),
                  XMLTYPE.bool.encode(p_date_modified),
                  XMLTYPE.bool.encode(expression_rid),
                  XMLTYPE.bool.encode(e_date_modified),
                  XMLTYPE.bool.encode(display_name),
                  XMLTYPE.bool.encode(dn_last_modified),
                  XMLTYPE.bool.encode(personal_status),
                  XMLTYPE.bool.encode(ps_last_modified),
                  XMLTYPE.bool.encode(user_tile_url),
                  XMLTYPE.bool.encode(photo),
                  XMLTYPE.bool.encode(flags)),
                 callback, errback)

    def _HandleGetProfileResponse(self, callback, errback, response, user_date):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def UpdateProfile(self, callback, errback):
        pass

    def _HandleUpdateProfileResponse(self, callback, errback, response, user_date):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def CreateRelationships(self, callback, errback):
        pass

    def _HandleCreateRelationshipsResponse(self, callback, errback, response, user_date):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def DeleteRelationships(self, callback, errback):
        pass

    def _HandleDeleteRelationshipsResponse(self, callback, errback, response, user_date):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def CreateDocument(self, callback, errback):
        pass

    def _HandleCreateDocumentResponse(self, callback, errback, response, user_date):
        pass

    @RequireSecurityTokens(LiveService.MESSENGER_CLEAR)
    def FindDocuments(self, callback, errback):
        pass

    def _HandleFindDocumentsResponse(self, callback, errback, response, user_date):
        pass

    def __soap_request(self, method, scenario, args, callback, errback):
        token = str(self._tokens[LiveService.MESSENGER_CLEAR])     

        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(scenario, token)
        soap_body = method.soap_body(*args)

        method_name = method.__name__.rsplit(".", 1)[1]
        self._send_request(method_name, 
                           self._service.url, 
                           soap_header, soap_body, soap_action, 
                           callback, errback, http_headers)

if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging
    from pymsn.service.SingleSignOn import *
    from pymsn.service.AddressBook import *

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
    
    def address_book_state_changed(address_book, pspec, sso):
        if address_book.state == AddressBookState.SYNCHRONIZED:

            def call(*arg):
                pass

            def err(*arg):
                pass

            storage = Storage(sso)
            storage.GetProfile(call, err, 'Initial', '2686986376622003804',
                               True, True, True, True, True, True, 
                               True, True, True, True, True)

    sso = SingleSignOn(account, password)
    address_book = AddressBook(sso)
    address_book.connect("notify::state", address_book_state_changed, sso)
    address_book.sync()

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
