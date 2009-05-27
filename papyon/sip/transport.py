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

from papyon.gnet.constants import *
from papyon.gnet.io import *

import gobject

class SIPTransport(gobject.GObject):

    __gsignals__ = {
        "connected": (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        "chunk-received": (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ([object]))
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

    @property
    def needs_registration(self):
        return True

    def open(self):
        self._client.open()
        gobject.timeout_add(5000, self.on_keep_alive)

    def on_keep_alive(self):
        self.send("\r\n\r\n\r\n\r\n", False)
        return True

    def send(self, message, log=True):
        if log:
            for line in message.splitlines():
                print ">>", line
        self._client.send(message)

    def on_received(self, client, message, len):
        for line in message.splitlines():
            print "<<", line
        self.emit("chunk-received", message)

    def on_status_changed(self, client, param):
        if self._client.status == IoStatus.OPEN:
            self.emit("connected")
        elif self._client.status == IoStatus.CLOSED:
            self.open()
