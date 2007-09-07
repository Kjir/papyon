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

from pymsn.msnp2p.constants import *
from pymsn.msnp2p.SLP import *
from pymsn.msnp2p.transport import *
import pymsn.profile

import pymsn.util.guid as guid
import base64
import random

__all__ = ['MSNObjectTransferSession']

MAX_INT32 = 0x7fffffff
MAX_INT16 = 0x7fff

def _generate_id(max=MAX_INT32):
    """
    Returns a random ID.

        @return: a random integer between 1000 and sys.maxint
        @rtype: integer
    """
    return random.randint(1000, max)


class P2PSessionInvite(object):
    def __init__(self, client, session, slp_request):
        self._session = session
        self._request = slp_request

        contacts = client.address_book.contacts.\
                search_by_network_id(pymsn.profile.NetworkID.MSN).\
                search_by_account(slp_request.frm)
        if len(contacts) == 0:
            contact = pymsn.profile.Contact(id=0,
                    network_id=pymsn.profile.NetworkID.MSN,
                    account=account,
                    display_name=account)
        else:
            contact = contacts[0]
        self.frm = contact
        self.to = client.profile

    def accept(self):
        self._respond(200)

    def reject(self):
        self._respond(603)

    def _respond(self, status_code):
        response = SLPResponseMessage(status_code,
                to = self.frm.account,
                frm = self.to.account,
                branch = self._request.branch,
                cseq = self._request.cseq + 1,
                branch = self._request.branch,
                call_id = self._request.call_id)
        self._session._send_p2p_data(response)


class P2PSession(object):
    def __init__(self, client, peer, euf_guid="", application_id=0):
        """Initializer"""
        self._client = client
        self._peer = peer

        self._euf_guid = euf_guid
        self._application_id = application_id

        self._call_id = None
        self._id = None

        self._transport = P2PTransportManager(self._client)
        self._transport.connect("blob-received", lambda tr, blob: self._on_blob_received(blob))
        self._transport.connect("blob-sent", lambda tr, blob: self._on_blob_sent(blob))

    @property
    def peer(self):
        return self._peer

    def invite(self, context):
        if self._call_id is None:
            self._call_id = "{%s}" % guid.generate_guid()
        if self._id is None:
            self._id = _generate_id()

        body = SLPMessageBody(SLPContentType.SESSION_REQUEST)
        body.add_header('EUF-GUID', self._euf_guid)
        body.add_header('SessionID', self._id)
        body.add_header('AppID', self._application_id)
        body.add_header('Context', str(context))

        message = SLPRequestMessage('INVITE',
                "MSNMSGR:" + self._peer.account,
                to = self._peer.account,
                frm = self._client.profile.account,
                branch = "{%s}" % guid.generate_guid(),
                cseq = 0,
                call_id = self._call_id)

        message.body = body
        self._send_p2p_data(message)

    def close(self):
        body = SLPMessageBody(SLPContentType.SESSION_CLOSE)

        message = SLPRequestMessage('BYE',
                "MSNMSGR:" + self._peer.account,
                to = self._peer.account,
                frm = self._client.profile.account,
                branch = "{%s}" % guid.generate_guid(),
                cseq = 0,
                call_id = self._call_id)
        message.body = body
        self._send_p2p_data(message)
        self._id = None
        self._call_id = None

    def _send_p2p_data(self, data_or_file):
        if isinstance(data_or_file, SLPMessage):
            session_id = 0
            data = str(data_or_file)
            total_size = len(data)
        else:
            session_id = self._id
            data = data_or_file
            total_size = None

        blob = MessageBlob(self._application_id,
                data, total_size, session_id)
        self._transport.send(self, blob)

    def _on_blob_sent(self, blob):
        pass

    def _on_blob_received(self, blob):
        if blob.session_id == 0:
            # FIXME: handle the signaling correctly
            pass
        elif blob.session_id != self._id:
            return
        elif blob.total_size == 4 and \
                blob.data.read() == ('\x00' * 4):
            self._on_data_preparation_blob_received(blob)
        else:
            self._on_data_blob_received(blob)
            self.close()

    def _on_data_preparation_blob_received(self, blob):
        pass

    def _on_data_blob_received(self, blob):
        pass


class MSNObjectTransferSession(P2PSession):
    def __init__(self, client, peer, application_id):
        P2PSession.__init__(self, client, peer,
                EufGuid.MSN_OBJECT, application_id)

    def request(self, msn_object):
        context = base64.b64encode(msn_object + "\x00")
        return P2PSession.invite(self, context)

    def _on_data_blob_received(self, blob):
        file = open("test.png", "w")
        file.write(blob.read())
        file.close()

