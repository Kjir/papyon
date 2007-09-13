# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
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

"""P2P
This module contains the classes needed to engage in a peer to peer transfer
with a contact."""

from event import EventsDispatcher
from msnp2p import OutgoingP2PSession, EufGuid, ApplicationID

import logging
import base64

__all__ = ['MSNObjectStore']

logger = logging.getLogger('p2p')

class MSNObjectStore(EventsDispatcher):
    def __init__(self, client):
        self._client = client
        self._outgoing_sessions = {} # session => (handle_id, callback, errback)
        self._incoming_sessions = {}
        EventsDispatcher.__init__(self)

    def request(self, contact, msn_object, callback, errback=None):
        context = base64.b64encode(msn_object + "\x00")
        # FIXME: we need to actually check the msn_object and select the appId accordingly
        application_id = ApplicationID.DISPLAY_PICTURE_TRANSFER
        session = OutgoingP2PSession(self._client._p2p_session_manager, contact,
                context, EufGuid.MSN_OBJECT, application_id)
        handle_id = session.connect("transfer-completed",
                        self._outgoing_session_transfer_completed)
        self._outgoing_sessions[session] = (handle_id, callback, errback)

    def publish(self, msn_object, file_object):
        pass
    
    def _outgoing_session_transfer_completed(self, session, data):
        handle_id, callback, errback = self._outgoing_sessions[session]
        session.disconnect(handle_id)
        callback[0](data, *callback[1:])
        del self._outgoing_sessions[session]
