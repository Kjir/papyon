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
import logging
import sys
import time
import unittest

sys.path.insert(0, "")

import papyon
from papyon.sip.conference import *
from papyon.sip.sip import *
from papyon.gnet.io.ssl_tcp import SSLTCPClient
from papyon.gnet.constants import *
from papyon.service.SingleSignOn import *
from papyon.transport import HTTPPollConnection

def get_proxies():
    import urllib
    proxies = urllib.getproxies()
    result = {}
    if 'https' not in proxies and \
            'http' in proxies:
        url = proxies['http'].replace("http://", "https://")
        result['https'] = papyon.Proxy(url)
    for type, url in proxies.items():
        if type == 'no': continue
        if type == 'https' and url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        result[type] = papyon.Proxy(url)
    return result

class SIPClient(papyon.Client):

    def __init__(self, account, password, invite):
        server = ('messenger.hotmail.com', 1863)
        papyon.Client.__init__(self, server, proxies = get_proxies())

        self.account = account
        self.password = password
        self.invite = invite
        self.conference = Conference()
        self.ttl = SSLTransport("vp.sip.messenger.msn.com", 443)
        self.sso = SingleSignOn(self.account, self.password)
        self.ttl.connect("connected", self.on_client_connected)
        self.connection = SIPConnection(self.ttl, self.sso, account, password)
        self._event_handler = ClientEvents(self, self.connection,
                self.conference)
        gobject.idle_add(self.connect)

    def connect(self):
        self.ttl.open()

    def on_client_connected(self, transport):
        self.login(self.account, self.password)


class ClientEvents(papyon.event.ClientEventInterface):

    def __init__(self, client, connection, conference):
        papyon.event.ClientEventInterface.__init__(self, client)
        self.connection = connection
        self.conference = conference

    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            self._client.quit()
        elif state == papyon.event.ClientState.OPEN:
            self._client.profile.display_name = "Louis-Francis"
            self._client.profile.presence = papyon.Presence.ONLINE
            for contact in self._client.address_book.contacts:
                print contact
            gobject.timeout_add(3000, self.invite)

    def invite(self):
        print "INVITE"
        call = self.connection.invite(invite)
        self.conference.setup(call)
        return False

    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error


class SSLTransport(gobject.GObject):

    __gsignals__ = {
        "connected": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "chunk-received": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([object]))
    }

    def __init__(self, host, port):
        gobject.GObject.__init__(self)
        self._host = host
        self._port = port
        self._protocol = "tls"
        self._client = SSLTCPClient(host, port)
        self._client.connect("received", self.on_received)
        self._client.connect("notify::status", self.on_status_changed)
        self._buffer = ""

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
        self.send("\r\n\r\n\r\n\r\n")
        return True

    def send(self, message):
        for line in message.splitlines():
            print ">>", line
        self._client.send(message)

    def on_received(self, client, message, len):
        for line in message.splitlines():
            print "<<", line
        self.emit("chunk-received", message)

    def on_status_changed(self, client, param):
        print "STATUS", self._client.status
        if self._client.status == IoStatus.OPEN:
            self.emit("connected")
        elif self._client.status == IoStatus.CLOSED:
            self.open()

if __name__ == "__main__":

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    if len(sys.argv) < 4:
        invite = raw_input('Invite: ')
    else:
        invite = sys.argv[3]

    logging.basicConfig(level=0)

    mainloop = gobject.MainLoop(is_running=True)
    client = SIPClient(account, password, invite)
    mainloop.run()
