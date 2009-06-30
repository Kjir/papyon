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
from papyon.media.conference import *
from papyon.media.constants import *
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

    def __init__(self, account, password, peer):
        server = ('messenger.hotmail.com', 1863)
        papyon.Client.__init__(self, server, proxies = get_proxies())

        self.peer = peer
        self._event_handler = ClientEvents(self)
        gobject.idle_add(self.login, account, password)

    def invite(self):
        contact = self.address_book.contacts.search_by_account(self.peer)[0]
        call = self.call_manager.create_call(contact)
        self.call_handler = CallEvents(call)
        self.session_handler = MediaSessionHandler(call.media_session)
        stream = call.media_session.create_stream("audio",
                MediaStreamDirection.BOTH, True)
        call.media_session.add_stream(stream)
        stream = call.media_session.create_stream("video",
                MediaStreamDirection.BOTH, True)
        call.media_session.add_stream(stream)
        call.invite()
        return False


class ClientEvents(papyon.event.ClientEventInterface,
                   papyon.event.InviteEventInterface):

    def __init__(self, client):
        papyon.event.ClientEventInterface.__init__(self, client)
        papyon.event.InviteEventInterface.__init__(self, client)

    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            self._client.quit()
        elif state == papyon.event.ClientState.OPEN:
            self._client.profile.display_name = "Paypon (SIP test)"
            self._client.profile.presence = papyon.Presence.ONLINE
            for contact in self._client.address_book.contacts:
                print contact
            gobject.timeout_add(2000, self._client.invite)

    def on_invite_conference(self, call):
        print "INVITED : call-id = %s" % call.id
        self.call_handler = CallEvents(call)
        self.session_handler = MediaSessionHandler(call.media_session)

    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error


class CallEvents(papyon.event.CallEventInterface):

    def __init__(self, call):
        papyon.event.CallEventInterface.__init__(self, call)

    def on_call_incoming(self):
        self._client.accept()

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
