# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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

from papyon.sip.sip import *
from papyon.sip.transport import *

import gobject

class SIPCallManager(gobject.GObject):

    __gsignals__ = {
        'invite-received': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ([object]))
    }

    server = "vp.sip.messenger.msn.com"
    port = 443

    def __init__(self, client, protocol):
        gobject.GObject.__init__(self)
        self._client = client
        self._protocol = protocol
        self._protocol.connect("buddy-notification-received",
                self.on_notification_received)
        self._connections = {}

    def create_connection(self, tunneled, host=None):
        account = self._client.profile.account
        if tunneled:
            transport = SIPTunneledTransport(self._protocol)
            connection = SIPTunneledConnection(transport, account)
        else:
            transport = SIPTransport(host, self.port)
            password = str(self._client.profile.password)
            sso = self._client._sso
            connection = SIPConnection(transport, sso, account, password)
        connection.connect("invite-received", self.on_invite_received)
        self._connections[host] = connection
        return connection

    def get_connection(self, tunneled, host=None):
        connection = self._connections.get(host, None)
        if connection is None:
            connection = self.create_connection(tunneled, host)
        return connection

    def invite(self, uri, tunneled=False):
        connection = self.get_connection(tunneled, self.server)
        call = connection.create_call()
        call.invite(uri)
        return call

    def on_notification_received(self, protocol, notification):
        if notification.arguments[1] != '2':
            return
        args = notification.payload.split()
        if len(args) == 3 and args[0] == "INVITE":
            # Register to the server so we can take the call
            connection = self.get_connection(False, args[1])
            connection.register(None, None)

    def on_invite_received(self, connection, call):
        self.emit("invite-received", call)
