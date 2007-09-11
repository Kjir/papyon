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

from pymsn.msnp2p.transport import *
from pymsn.msnp2p.exceptions import ParseError
from pymsn.msnp2p.SLP import SLPMessage, SLPRequestMessage, SLPResponseMessage
from pymsn.msnp2p.session import IncomingP2PSession

import pymsn.profile

import gobject
import weakref
import logging

__all__ = ['P2PSessionManager']

logger = logging.getLogger('msnp2p:session-manager')

class P2PSessionManager(gobject.GObject):
    __gsignals__ = {
            "incoming-session" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
    }

    def __init__(self, client):
        """Initializer"""
        gobject.GObject.__init__(self)

        self._client = client
        self._sessions = weakref.WeakValueDictionary() # session_id => session
        self._transport_manager = P2PTransportManager(self._client)
        self._transport_manager.connect("blob-received", lambda tr, blob: self._on_blob_received(blob))
        self._transport_manager.connect("blob-sent", lambda tr, blob: self._on_blob_sent(blob))

    def _register_session(self, session):
        self._sessions[session.id] = session

    def _unregister_session(self, session):
        del self._sessions[session.id]

    def _blob_to_session(self, blob, create_inexistant_session=True):
        if blob.session_id == 0:
            slp_data = blob.data.read()
            blob.data.seek(0, 0)
            try:
                message = SLPMessage.build(slp_data)
            except ParseError:
                logger.warning('Received blob with SessionID=0 and non SLP data')
                #TODO: answer with a 500 Internal Error ?
                return None
            session_id = message.body.session_id
            if session_id in self._sessions:
                return self._sessions[session_id]

            if isinstance(message, SLPRequestMessage) and message.method == 'INVITE':
                if not create_inexistant_session:
                    logger.warning('Received blob SLP INVITE, but Session spawning disabled')
                    return None

                contacts = self._client.address_book.contacts.\
                        search_by_network_id(pymsn.profile.NetworkID.MSN).\
                        search_by_account(message.frm)
                if len(contacts) == 0:
                    peer = pymsn.profile.Contact(id=0, 
                            network_id=pymsn.profile.NetworkID.MSN, 
                            account=message.frm, 
                            display_name=message.frm)
                else:
                    peer = contacts[0]
                session = IncomingP2PSession(self, peer,
                        session_id, message.call_id,
                        message.body.euf_guid, message.body.application_id,
                        message.cseq, message.branch)
                self.emit("incoming-session", session)
                return session
            else:
                logger.warning('Received initial blob with SessionID=0 and non INVITE SLP data')
                #TODO: answer with a 500 Internal Error ?
                return None
        else:
            session_id = blob.session_id
            if session_id in self._sessions:
                return self._sessions[blob.session_id]
            else:
                logger.warning('Received blob with unknown session ID')
                #TODO: answer with a 500 Internal Error ?
                return None

    def _on_blob_received(self, blob):
        session = self._blob_to_session(blob, True)
        if session is None:
            return
        session._on_blob_received(blob)

    def _on_blob_sent(self, blob):
        session = self._blob_to_session(blob, False)
        if session is None:
            return
        session._on_blob_sent(blob)

gobject.type_register(P2PSessionManager)
