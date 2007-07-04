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
import oim
import rsi

import gobject

__all__ = ['OfflineIM']

class OfflineIM(gobject.GObject):
    """abstraction class to the offline messages stuff
    """

    def __init__(self, passport_security_token, http_proxy=None):
        gobject.GObject.__init__(self)
        self._oim_client = oim.OIMService(passport_security_token, http_proxy)
        self._rsi_client = rsi.RSIService(passport_security_token, http_proxy)

        self._sequence_number = 1
        self.messages = []
        
    def send(self, source, fname, recipient, content):
        """Send an offline message.

           @param recipient : the passport address of the recipient
           @param content : the content of the message
        """
        print 'send OIM to %s with content %s' % (recipient, content)
        self._oim_client.Store(source, fname, recipient, 
                               self._sequence_number,
                               self._oim_send_cb)
        self._sequence_number += 1

    def retrieve(self):
        """Retrieve received offline messages from the server, based
        on the information parsed from the metadata chunks.
        
        """
        pass

    def delete(self, id):
        """Delete a received offline message from the server.

           @param id : the id of the message to delete
        """
        pass

    def _get_metadata(self):
        """Retrieve the metadata from the server using a SOAP action.
        This is used when more than 25 OIM are stored on the server.
        
        """
        pass

    def _parse_mail_data(self, mail_data):
        """Used to parse the metadata chunk received in the notification
        or in response to the SOAP action.
        """
        pass

    def _build_mail_data(self):
        """Used to build the mail formatted data when sending OIMs.
        """
        pass

    # Callbacks
    def _oim_send_cb(self, soap_response):
        pass

gobject.type_register(OfflineIM)
    
