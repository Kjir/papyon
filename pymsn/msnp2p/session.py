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

def _generate_guid():
    bytes = [random.randrange(256) for i in range(16)]

    data1 = ("%02X" * 4) % tuple(bytes[0:4])
    data2 = ("%02X" * 2) % tuple(bytes[4:6])
    data3 = ("%02X" * 2) % tuple(bytes[6:8])
    data4 = ("%02X" * 2) % tuple(bytes[8:10])
    data5 = ("%02X" * 6) % tuple(bytes[10:])

    data3 = "4" + data3[1:]

    return "{%s-%s-%s-%s-%s}" % (data1, data2, data3, data4, data5)


class SessionInvite(object):
    def __init__(self, client, slp_message):
        pass

class P2PSession(object):
    def __init__(self, client, peer, euf_guid="", application_id=0):
        """Initializer"""
        self._client = client
        self._peer = peer

        self._euf_guid = euf_guid
        self._application_id = application_id

        self._call_id = None
        self._session_id = None

        #FIXME: implement the transport manager and get rid of this
        self._transport = None

    def invite(self, context):
        if self._call_id is None:
            self._call_id = _generate_guid()
        if self._session_id is None:
            self._session_id = _generate_id()

        self._transport = SwitchboardP2PTransport(self._client, self._peer)

        body = SLPMessageBody(SLPContentType.SESSION_REQUEST)
        body.add_header('EUF-GUID', self._euf_guid)
        body.add_header('SessionID', self._session_id)
        body.add_header('AppID', self._application_id)
        body.add_header('Context', str(context))

        message = SLPRequestMessage('INVITE',
                to = self._peer.account,
                frm = self._client.profile.account,
                branch = _generate_guid(),
                cseq = 0,
                call_id = self._call_id)

        message.body = body
        self._send_p2p_data(message)

    def close(self):
        body = SLPMessageBody(SLPContentType.SESSION_CLOSE)

        message = SLPRequestMessage('BYE',
                to = self._peer.account,
                frm = self._client.profile.account,
                branch = _generate_guid(),
                cseq = 0,
                call_id = self._call_id)
        message.body = body
        self._send_p2p_data(message)

    def _send_p2p_data(self, data_or_file):
        if isinstance(data_or_file, SLPMessage):
            session_id = 0
            data = str(data_or_file)
            total_size = len(data)
        else:
            session_id = self._session_id
            data = data_or_file
            total_size = None

        blob = MessageBlob(self._application_id,
                data, total_size, session_id)
        self._transport.send(blob)

    def _on_invite_response(self, response):
        pass


class MSNObjectTransferSession(object):
    def __init__(self, client, application_id):
        SLPSession.__init__(self, client,
                constants.EufGuid.MSNOBJECT, application_id)
