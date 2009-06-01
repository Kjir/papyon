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
from papyon.sip.sip import SIPMessageParser

import base64
import gobject
import xml.dom.minidom

class SIPBaseTransport(gobject.GObject):

    __gsignals__ = {
        "message-received": (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ([object]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self._parser = SIPMessageParser()
        self._parser.connect("message-parsed", self.on_message_parsed)

    def on_message_parsed(self, parser, message):
        self.emit("message-received", message)

    def send(self, message):
        raise NotImplementedError

    def log_message(self, prefix, message):
        for line in message.splitlines():
            print prefix, line


class SIPTransport(SIPBaseTransport):

    def __init__(self, host, port):
        SIPBaseTransport.__init__(self)
        self._client = SSLTCPClient(host, port)
        self._client.connect("received", self.on_received)
        self._client.connect("notify::status", self.on_status_changed)
        self._alive_src = None
        self._closing = False
        self._msg_queue = []

    @property
    def protocol(self):
        return "tls"

    def send(self, message):
        data = str(message)
        if self._client.status == IoStatus.OPEN:
            self.log_message(">>", data)
            self._send(data)
        else:
            self._msg_queue.append(message)
            self._open()

    def _open(self):
        if self._client.status == IoStatus.OPEN:
            return
        self._close()
        self._closing = False
        self._client.open()
        self._start_keep_alive()

    def _close(self):
        if self._client.status == IoStatus.CLOSED:
            return
        self._stop_keep_alive()
        self._closing = True
        self._client.close()

    def _send(self, data):
        self._client.send(data)

    def _start_keep_alive(self):
        self._alive_src = gobject.timeout_add(5000, self._on_keep_alive)

    def _stop_keep_alive(self):
        if self._alive_src is not None:
            gobject.source_remove(self._alive_src)
            self._alive_src = None

    def _on_keep_alive(self):
        if self._client.status == IoStatus.OPEN:
            self._send("\r\n\r\n\r\n\r\n")
            return True
        else:
            return False

    def on_received(self, client, chunk, len):
        self.log_message("<<", chunk)
        self._parser.append(chunk)

    def on_status_changed(self, client, param):
        if self._client.status == IoStatus.OPEN:
            while self._msg_queue:
                self.send(self._msg_queue.pop(0))
        elif self._client.status == IoStatus.CLOSED:
            if not self._closing:
                self._open()


class SIPTunneledTransport(SIPBaseTransport):

    def __init__(self, protocol):
        SIPBaseTransport.__init__(self)
        self._protocol = protocol
        self._protocol.connect("buddy-notification-received",
                self.on_notification_received)

    @property
    def protocol(self):
        return "tcp"

    def send(self, message):
        call_id = message.call.id
        contact = message.call.contact
        self.log_message(">>", str(message))
        data = base64.b64encode(str(message))
        data = '<sip e="base64" fid="1" i="%s"><msg>%s</msg></sip>' % \
                (call_id, data)
        data = data.replace("\r\n", "\n").replace("\n", "\r\n")
        self._protocol.send_user_notification(data, contact, 12)

    def on_notification_received(self, protocol, notification):
        if notification.arguments[1] != '12':
            return
        doc = xml.dom.minidom.parseString(notification.payload)
        chunk = doc.getElementsByTagName("msg")[0].firstChild.data
        chunk = base64.b64decode(chunk)
        self.log_message("<<", chunk)
        self._parser.append(chunk)
        doc.unlink()
