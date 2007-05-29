# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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

"""Conversation
This module contains the class needed to have a conversation with a
contact."""

from transport import *
from event import ClientState, ClientErrorType

import msnp

import logging
import gobject

__all__ = ['Conversation']

logger = logging.getLogger('conversation')

class Conversation(object):
    """This class provides way to connect to the switchboard server."""

    def __init__(self, client, session=None):
        """Initializer

            @param client: the parent client instance
            @type client: L{pymsn.Client}
            
            @param session: the session to join or None
            @type session: tuple(server, session_id, key) or None"""
        self._client = client
        self._transport = None
        self._protocol = None
        self._events_handlers = set()
        self._state = ClientState.CONNECTING
        if session is None:
            gobject.idle_add(self.__request_switchboard)
        else:
            gobject.idle_add(self.__open, session)
        self.__action_queue = []

    def __setup_callbacks(self):
        self._transport.connect("connection-success", self._on_connect_success)
        self._transport.connect("connection-failure", self._on_connect_failure)
        self._transport.connect("connection-lost", self._on_disconnected)

        self._protocol.connect("notify::state", self._on_protocol_state_changed)

    def __open(self, session):
        print "*********", session
        server, session_id, key = session
        transport_class = self._client._transport_class
        self._transport = transport_class(server, ServerType.SWITCHBOARD,
                self._client._proxies)
        self._protocol = msnp.SwitchboardProtocol(self, self._transport,
                session_id, key, proxies=self._client._proxies)
        self.__setup_callbacks()
        
        self._transport.establish_connection()
        return False
    
    def __request_switchboard(self):
        self._client._protocol.request_switchboard(self.__open)
        return False

    def _get_state(self):
        return self.__state
    def _set_state(self, state):
        self.__state = state
        self._dispatch("on_conversation_state_changed", state)
    state = property(_get_state)
    _state = property(_get_state, _set_state)
    
    ### Public API
    def send_text_message(self, text):
        """Build and send a text message to all persons in this
        switchboard.
        
            @param text: the text message to send.
            @type text: string"""
        self.__queue_action(self._do_send_text_message, text)

    def invite_user(self, contact):
        """Request a contact to join in the conversation.
            
            @param contact: the contact to invite.
            @type contact: L{profile.Contact}"""
        self.__queue_action(self._do_invite_contact, contact)

    def leave_conversation(self):
        """Leave the conversation."""
        #:TODO: enhance this
        if self._protocol and self._protocol.state == msnp.ProtocolState.OPEN:
            self._protocol.leave_conversation()
    
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
        self._dispatch("on_conversation_error", ClientErrorType.NETWORK, reason)
        self._state = ClientState.CLOSED

    def _on_disconnected(self, transp, reason):
        self._dispatch("on_conversation_error", ClientErrorType.NETWORK, reason)
        if self._protocol.state != msnp.ProtocolState.IDLE:
            self._state = ClientState.CLOSED

    # - - Switchboard Protocol
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
            self.__process_action_queue()
        elif state == msnp.ProtocolState.IDLE:
            pass
    
    # - - Queue
    def __push_action(self, action, *args):
        self.__action_queue.append((action, args))
        self.__process_action_queue()
    
    def __process_action_queue(self):
        if self._protocol is not None:
            protocol_state = self._protocol.state
        else:
            protocol_state = msnp.ProtocolState.CLOSED
        
        if protocol_state == msnp.ProtocolState.OPEN:
            for action, args in self.__action_queue:
                action(*args)
            self.__action_queue = []
        elif protocol_state == msnp.ProtocolState.CLOSED or\
                protocol_state == msnp.ProtocolState.IDLE:
            gobject.idle_add(self.__request_switchboard)
    
    # - - Actions
    def _do_invite_contact(self, contact):
        self._protocol.invite_user(contact)

    def _do_send_text_message(self, text):
        msg = msnp.OutgoingMessage(self._transport.transaction_id,
                msnp.MessageAcknowledgement.HALF)
        msg.content_type = ("text/plain","UTF-8")
        msg.body = text.encode('UTF-8')
        self._protocol.send_message(msg)
        

