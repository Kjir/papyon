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
        self._client = SSLTCPClient(host, port)
        self._client.connect("received", self.on_received)
        self._client.connect("notify::status", self.on_status_changed)
        self._alive_src = None
        self._closing = False
        self._msg_queue = []

    @property
    def protocol(self):
        return "tls"

    def open(self):
        if self._client.status == IoStatus.OPEN:
            return
        self.close()
        self._closing = False
        self._client.open()
        self.start_keep_alive()

    def close(self):
        if self._client.status == IoStatus.CLOSED:
            return
        self.stop_keep_alive()
        self._closing = True
        self._client.close()

    def start_keep_alive(self):
        self._alive_src = gobject.timeout_add(5000, self.on_keep_alive)

    def stop_keep_alive(self):
        if self._alive_src is not None:
            gobject.remove_source(self._alive_src)
            self._alive_src = None

    def on_keep_alive(self):
        self.send("\r\n\r\n\r\n\r\n", True)
        return True

    def send(self, message, ping=False):
        if self._client.status == IoStatus.OPEN:
            if not ping:
                self.log_message(">>", message)
            self._client.send(message)
        elif not ping:
            self._msg_queue.append(message)
            self.open()

    def on_received(self, client, message, len):
        self.log_message("<<", message)
        self.emit("chunk-received", message)

    def on_status_changed(self, client, param):
        if self._client.status == IoStatus.OPEN:
            self.emit("connected")
            while self._msg_queue:
                self.send(self._msg_queue.pop())
        elif self._client.status == IoStatus.CLOSED:
            if not self._closing:
                self.open()

    def log_message(self, prefix, message):
        for line in message.splitlines():
            print prefix, line
