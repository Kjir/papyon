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
from papyon.sip.transport import *
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

    def __init__(self, account, password, invited):
        server = ('messenger.hotmail.com', 1863)
        papyon.Client.__init__(self, server, proxies = get_proxies())

        self.invited = invited
        self.conference = Conference()
        self.ttl = SIPTransport("vp.sip.messenger.msn.com", 443)
        self.sso = SingleSignOn(account, password)
        self.connection = SIPConnection(self.ttl, self.sso, account, password)
        self._event_handler = ClientEvents(self, self.conference)
        gobject.idle_add(self.login, account, password)

    def invite(self):
        call = self.call_manager.invite(self.invited)
        self.conference.setup(call)
        return False


class ClientEvents(papyon.event.ClientEventInterface,
                   papyon.event.InviteEventInterface):

    def __init__(self, client, conference):
        papyon.event.ClientEventInterface.__init__(self, client)
        papyon.event.InviteEventInterface.__init__(self, client)
        self.conference = conference

    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            self._client.quit()
        elif state == papyon.event.ClientState.OPEN:
            self._client.profile.display_name = "Paypon (SIP test)"
            self._client.profile.presence = papyon.Presence.ONLINE
            for contact in self._client.address_book.contacts:
                print contact
            #gobject.timeout_add(2000, self._client.invite)

    def on_invite_conference(self, call):
        print "INVITED : call-id = %s" % call.get_call_id()
        self.conference.setup(call)

    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error

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
