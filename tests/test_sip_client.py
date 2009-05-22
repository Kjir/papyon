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

import getpass
import gobject
import sys
import time
import unittest

sys.path.insert(0, "")

from papyon.sip.sip import *
from papyon.service.description.SingleSignOn.RequestMultipleSecurityTokens import LiveService
from papyon.gnet.io.ssl_tcp import SSLTCPClient
from papyon.gnet.constants import *
from papyon.service.SingleSignOn import *

class SIPClient(object):

    def __init__(self, account, password):
        self.ttl = SSLTransport("vp.sip.messenger.msn.com", 443)
        self.ttl.connect("connected", self.on_client_connected)
        self.connection = SIPConnection(self.ttl, None, None)
        self.account = account
        self.password = password
        gobject.idle_add(self.connect)

    def connect(self):
        self.ttl.open()

    def on_client_connected(self, transport):
        sso = SingleSignOn(self.account, self.password)
        sso.RequestMultipleSecurityTokens((self.on_token_received, ), None,
                LiveService.MESSENGER_SECURE)

    def on_token_received(self, tokens):
        ticket = tokens[LiveService.MESSENGER_SECURE]
        self.connection.register(self.account, ticket)


class SSLTransport(gobject.GObject):

    __gsignals__ = {
        "connected": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "line-received": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([object]))
    }

    def __init__(self, host, port):
        gobject.GObject.__init__(self)
        self._host = host
        self._port = port
        self._protocol = "tls"
        self._client = SSLTCPClient(host, port)
        self._client.connect("received", self.on_received)
        self._client.connect("notify::status", self.on_status_changed)

    @property
    def ip(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def protocol(self):
        return self._protocol

    def open(self):
        self._client.open()

    def send(self, message):
        for line in message.splitlines():
            print ">>", line
        self._client.send(message)

    def on_received(self, client, message, len):
        for line in message.splitlines():
            print "<<", line
            self.emit("line-received", line)

    def on_status_changed(self, client, param):
        print "STATUS", self._client.status
        if self._client.status == IoStatus.OPEN:
            self.emit("connected")

if __name__ == "__main__":

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)
    client = SIPClient(account, password)
    mainloop.run()
