# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2006  Ole André Vadla Ravnås <oleavr@gmail.com>
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

"""Client
This module contains classes that clients should use in order to make use
of the library."""

from transport import *
from event import ClientState, ClientErrorType

import profile
import msnp

import logging

__all__ = ['Client']

logger = logging.getLogger('client')

class Client(object):
    """This class provides way to connect to the notification server as well
    as methods to manage the contact list, and the personnal settings.

    Basically you should inherit from this class and implement the callbacks
    in order to build a client.

    @group Connection: login, logout"""

    def __init__(self, server, proxies={}, transport_class=DirectConnection):
        """Initializer

            @param server: the Notification server to connect to.
            @type server: tuple(host, port)

            @param proxies: proxies that we can use to connect
            @type proxies: {type: string => L{gnet.proxy.ProxyInfos}}"""
        self.__state = ClientState.CLOSED
        self._account = None
        self._proxies = proxies
        self._transport = transport_class(server, ServerType.NOTIFICATION,
                self._proxies)
        self._protocol = msnp.NotificationProtocol(self, self._transport,
                self._proxies)

        self.profile = None
        self.address_book = None # FIXME: update when the addressbook get updated

        self._events_handlers = set()
        self.__setup_callbacks()

    def __setup_callbacks(self):
        self._transport.connect("connection-success", self._on_connect_success)
        self._transport.connect("connection-failure", self._on_connect_failure)
        self._transport.connect("connection-lost", self._on_disconnected)

        self._protocol.connect("notify::state", self._on_protocol_state_changed)

    def _get_state(self):
        return self.__state
    def _set_state(self, state):
        self.__state = state
        self._dispatch("on_client_state_changed", state)
    state = property(_get_state)
    _state = property(_get_state, _set_state)

    ### public methods & properties
    def login(self, account, password):
        """Login to the server.

            @param account: the account to use for authentication.
            @type account: string

            @param password: the password needed to authenticate to the account
            """
        assert(self._state == ClientState.CLOSED, "Login already in progress")

        self._account = (account, password)
        self.profile = profile.User(self._account, self._protocol)
        self._transport.establish_connection()
        self._state = ClientState.CONNECTING

    def logout(self):
        """Logout from the server."""
        self._protocol.signoff()

    ### Callbacks
    def register_events_handler(self, events_handler):
        """
        events_handler:
            an instance with methods as code of callbacks.
        """
        self._events_handlers.add(events_handler)

    def _dispatch(self, name, *args):
        for event_handler in self._events_handlers:
            event_handler._dispatch_event(name, *args)

    # - - Transport
    def _on_connect_success(self, transp):
        self._state = ClientState.CONNECTED

    def _on_connect_failure(self, transp, reason):
        self._dispatch("on_client_error", ClientErrorType.NETWORK, reason)
        self._state = ClientState.CLOSED

    def _on_disconnected(self, transp, reason):
        self._dispatch("on_client_error", ClientErrorType.NETWORK, reason)
        self._state = ClientState.CLOSED

    # - - Notification Protocol
    def _on_protocol_state_changed(self, proto, param):
        state = proto.state
        if state == msnp.ProtocolState.AUTHENTICATING:
            self._state = ClientState.AUTHENTICATING
        elif state == msnp.ProtocolState.AUTHENTICATED:
            self._state = ClientState.AUTHENTICATED
        elif state == msnp.ProtocolState.SYNCHRONIZING:
            self._state = ClientState.SYNCHRONIZING
        elif state == msnp.ProtocolState.SYNCHRONIZED:
            self._state = ClientState.SYNCHRONIZED
        elif state == msnp.ProtocolState.OPEN:
            self._state = ClientState.OPEN

