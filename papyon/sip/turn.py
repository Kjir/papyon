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
from papyon.gnet.io.ssl_tcp import SSLTCPClient
from papyon.service.SingleSignOn import *
from papyon.util.decorator import rw_property

import base64
import getpass
import gobject
import hashlib
import hmac
import md5
import random
import struct
import sys

MESSAGE_TYPES = {
    1: "BINDING-REQUEST",
    2: "SHARED-SECRET-REQUEST",
    3: "ALLOCATE-REQUEST",
    257: "BINDING-RESPONSE",
    258: "SHARED-SECRET-RESPONSE",
    259: "ALLOCATE-RESPONSE",
    273: "BINDING-ERROR",
    274: "SHARED-SECRET-ERROR",
    275: "ALLOCATE-ERROR"
}

ATTRIBUTE_TYPES = {
    1: "MAPPED-ADDRESS",
    2: "RESPONSE_ADDRESS",
    3: "CHANGE_REQUEST",
    4: "SOURCE_ADDRESS",
    5: "CHANGED-ADDRESS",
    6: "USERNAME",
    7: "PASSWORD",
    8: "MESSAGE-INTEGRITY",
    9: "ERROR-CODE",
    10: "UNKNOWN-ATTRIBUTES",
    11: "REFLECTED-FROM",
    12: "TRANSPORT-PREFERENCES",
    13: "LIFETIME",
    14: "ALTERNATE-SERVER",
    15: "MAGIC-COOKIE",
    16: "BANDWIDTH",
    17: "MORE-AVAILABLE",
    18: "REMOTE-ADDRESS",
    19: "DATA",
    20: "REALM",
    21: "NONCE",
    22: "RELAY-ADDRESS",
    23: "REQUESTED-ADDRESS-TYPE",
    24: "REQUESTED-PORT",
    25: "REQUESTED-TRANSPORT",
    26: "XOR-MAPPED-ADDRESS",
    27: "TIMER-VAL",
    28: "REQUESTED-IP",
    29: "FINGERPRINT",
    32802: "SERVER",
    32803: "ALTERNATE-SERVER",
    32804: "REFRESH-INTERVAL"
}

class TURNClient(object):

    host = "relay.voice.messenger.msn.com"
    port = 443

    def __init__(self, sso, account):
        self._transport = SSLTCPClient(self.host, self.port)
        self._transport.connect("notify::status", self.on_status_changed)
        self._transport.connect("received", self.on_message_received)
        self._msg_queue = []
        self._requests = {}
        self._relays = []
        self._account = account
        self._sso = sso
        self._tokens = {}

    def send(self, message):
        self._requests[message.id] = message
        if self._transport.status != IoStatus.OPEN:
            self._msg_queue.append(message)
            self._transport.open()
            return
        self._transport.send(str(message))

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def request_shared_secret(self, callback, errcb, count=4):
        for _ in range(count):
            token = self._tokens[LiveService.MESSENGER_SECURE]
            attrs = [TURNAttribute("USERNAME", "RPS_%s\x00\x00\x00" % token)]
            msg = TURNMessage("SHARED-SECRET-REQUEST", attrs)
            self.send(msg)

    def request_shared_secret_with_integrity(self, realm, nonce):
        token = self._tokens[LiveService.MESSENGER_SECURE]
        attrs = [TURNAttribute("USERNAME", "RPS_%s\x00\x00\x00" % token),
                 TURNAttribute("REALM", realm),
                 TURNAttribute("NONCE", nonce)]
        msg = TURNMessage("SHARED-SECRET-REQUEST", attrs, 24)
        hmac = self.build_message_integrity(msg, nonce)
        msg.attributes.append(TURNAttribute("MESSAGE-INTEGRITY", hmac))
        msg.extra_size = 0
        self.send(msg)

    def build_message_integrity(self, msg, nonce):
        token = self._tokens[LiveService.MESSENGER_SECURE]
        nonce = nonce.strip("\"")
        m = md5.new()
        m.update("RPS_%s\x00\x00\x00:" % token)
        m.update("%s:%s" % (nonce, self._account))
        key = m.digest() + ("\x00" * 16)

        msg = str(msg)
        padding = 64 - (len(msg) % 64)
        if padding is 64:
            padding = 0
        msg += "\x00" * padding

        h = hmac.new(key, msg, hashlib.sha1)
        return h.digest()

    def on_status_changed(self, transport, param):
        if self._transport.status == IoStatus.OPEN:
            while self._msg_queue:
                self.send(self._msg_queue.pop())

    def on_message_received(self, transport, data, length):
        msg = TURNMessage()
        msg.parse(data)

        if self._requests.get(msg.id, None) is None:
            return
        else:
            del self._requests[msg.id]

        if msg.type == "SHARED-SECRET-ERROR":
            for attr in msg.attributes:
                if attr.type == "REALM":
                    realm = attr.value
                elif attr.type == "NONCE":
                    nonce = attr.value
                elif attr.type == "ERROR-CODE":
                    error_msg = attr.value[4:]
            if error_msg == "Unauthorized":
                self.request_shared_secret_with_integrity(realm, nonce)

        elif msg.type == "SHARED-SECRET-RESPONSE":
            relay = TURNRelay()
            for attr in msg.attributes:
                if attr.type == "USERNAME":
                    relay.username = base64.b64encode(attr.value)
                elif attr.type == "PASSWORD":
                    relay.password = base64.b64encode(attr.value)
                elif attr.type == "ALTERNATE-SERVER":
                    server = struct.unpack("!HHcccc", attr.value)
                    ip = map(lambda x: ord(x), server[2:6])
                    relay.ip = "%i.%i.%i.%i" % tuple(ip)
                    relay.port = server[1]
            self._relays.append(relay)

        if not self._requests:
            self._transport.close()
            print self._relays


class TURNMessage(object):

    def __init__(self, type=None, attributes=[], extra_size=0):
        self.type = type
        self._attributes = attributes
        self._extra_size = extra_size
        self._id = self.gen_id()

    @property
    def id(self):
        return self._id

    @rw_property
    def type():
        def fget(self):
            return MESSAGE_TYPES.get(self._type, None)
        def fset(self, value):
            self._type = None
            for k,v in MESSAGE_TYPES.iteritems():
                if v == value:
                    self._type = k
        return locals()

    @property
    def attributes(self):
        return self._attributes

    @rw_property
    def extra_size():
        def fget(self):
            return self._extra_size
        def fset(self, value):
            self._extra_size = value
        return locals()

    def gen_id(self):
        #FIXME Should be a 128 bits random id
        return 400000000 + random.randint(0,2000000)

    def split_id(self):
        parts = []
        id = self._id
        for i in range(0, 4):
            parts.append(int(id & 0xFFFFFFFF))
            id >>= 32
        parts.reverse()
        return parts

    def merge_id(self, parts):
        self._id = 0
        for part in parts:
            self._id += part
            self._id <<= 32
        self._id >>= 32

    def parse(self, msg):
        hdr = struct.unpack("!HH4I", msg[0:20])
        self._type = hdr[0]
        self.merge_id(hdr[2:])

        msg = msg[20:]
        while msg:
            attr = TURNAttribute()
            attr.parse(msg)
            self._attributes.append(attr)
            msg = msg[len(attr):]

    def __str__(self):
        msg = ""
        for attr in self._attributes:
            msg += str(attr)
        id = self.split_id()
        hdr = struct.pack("!HH4I", self._type, len(msg) + self._extra_size,
                          id[0], id[1], id[2], id[3])
        return (hdr + msg)


class TURNAttribute(object):

    def __init__(self, type=None, value=None):
        self.type = type
        self._value = value

    @rw_property
    def type():
        def fget(self):
            return ATTRIBUTE_TYPES.get(self._type, None)
        def fset(self, value):
            self._type = None
            for k,v in ATTRIBUTE_TYPES.iteritems():
                if v == value:
                    self._type = k
                    break
        return locals()

    @property
    def value(self):
        return self._value

    def parse(self, msg):
        type, size = struct.unpack("!HH", msg[0:4])
        self._type = type
        self._value = msg[4:size+4]

    def __len__(self):
        return len(self._value) + 4

    def __str__(self):
        attr = struct.pack("!HH", self._type, len(self._value))
        attr += self._value
        return attr


class TURNRelay(object):

    def __init__(self):
        self.username = None
        self.password = None
        self.ip = None
        self.port = None

    def __repr__(self):
        return "<TURN Relay: %s %i>" % (self.ip, self.port)


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
    sso = SingleSignOn(account, password)
    client = TURNClient(sso, account)
    client.request_shared_secret(None, None, 2)
    mainloop.run()
