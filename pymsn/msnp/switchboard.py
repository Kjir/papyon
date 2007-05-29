# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2005-2006 Ole André Vadla Ravnås <oleavr@gmail.com> 
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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

"""Switchboard protocol Implementation
Implements the protocol used to communicate with the Switchboard Server."""

from base import BaseProtocol, ProtocolState
from message import IncomingMessage
import pymsn.profile

import logging
import urllib 
import gobject

__all__ = ['SwitchboardProtocol']

logger = logging.getLogger('protocol:switchboard')


class SwitchboardProtocol(BaseProtocol, gobject.GObject):
    """Protocol used to communicate with the Switchboard Server
        
        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler

        @ivar _state: the current protocol state
        @type _state: integer
        @see L{ProtocolState}"""
    __gsignals__ = {
            "message-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            
            "message-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "message-delivered": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "message-undelivered": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "user-joined": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "user-left": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))}

    __gproperties__ = {
            "state":  (gobject.TYPE_INT,
                "State",
                "The state of the communication with the server.",
                0, 7, ProtocolState.CLOSED,
                gobject.PARAM_READABLE)
            }

    def __init__(self, conversation, transport, session_id, key=None, proxies={}):
        """Initializer

            @param conversation: the parent object
            @type conversation: L{conversation.Conversation}

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}
            
            @param session_id: the session to join if any
            @type session_id: string

            @param key: the key used to authenticate to server when connecting
            @type key: string

            @param proxies: a dictonary mapping the proxy type to a
                L{gnet.proxy.ProxyInfos} instance
            @type proxies: {type: string, proxy:L{gnet.proxy.ProxyInfos}}
        """
        BaseProtocol.__init__(self, conversation, transport, proxies)
        gobject.GObject.__init__(self)
        self.participants = {}
        self._conversation = self._client
        self.__session_id = session_id
        self.__key = key
        self.__state = ProtocolState.CLOSED
    
    # Properties ------------------------------------------------------------
    def __get_state(self):
        return self.__state
    def __set_state(self, state):
        self.__state = state
        self.notify("state")
    state = property(__get_state)
    _state = property(__get_state, __set_state)
        
    def do_get_property(self, pspec):
        if pspec.name == "state":
            return self.__state
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name
    
    # Public API -------------------------------------------------------------        
    def invite_user(self, contact):
        """Invite user to join in the conversation
            
            @param contact: the contact to invite
            @type contact: L{profile.Contact}"""
        assert(self.state == ProtocolState.OPEN)
        self._transport.send_command_ex('CAL', (contact.account,) )

    def send_message(self, message, callback=None, cb_args=()):
        """Send a message to all contacts in this switchboard
        
            @param message: the message to send
            @type message: L{message.OutgoingMessage}"""
        assert(self.state == ProtocolState.OPEN)
        our_cb_args = (message, callback, cb_args)
        self._transport.send_command(message,
                callback=self.__on_message_sent, cb_args=our_cb_args)

    def __on_message_sent(self, message, user_callback, user_cb_args):
        self.emit("message-sent", message)
        if user_callback:
            user_callback(*user_cb_args)

    def leave_conversation(self):
        """Leave the conversation"""
        assert(self.state == ProtocolState.OPEN)
        self._transport.send_command_ex('OUT')
    # Handlers ---------------------------------------------------------------
    # --------- Authentication -----------------------------------------------
    def _handle_ANS(self, command):
        self._state = ProtocolState.AUTHENTICATED
        if command.arguments[0] == 'OK':
            self._state = ProtocolState.OPEN
        else:
            self._state = ProtocolState.SYNCHRONIZING

    def _handle_USR(self, command):
        self._state = ProtocolState.AUTHENTICATED
        self._state = ProtocolState.OPEN
    
    def _handle_OUT(self, command):
        pass
    # --------- Invitation ---------------------------------------------------
    def __participant_join(self, account, display_name, client_id):
        contacts = self._conversation._client.addressbook.contacts.\
                search_by_account(account)
        if len(contacts) == 0:
            contact = pymsn.profile.Contact(id=0,
                    network_id=pymsn.profile.NetworkID.MSN,
                    account=account,
                    display_name=display_name)
        else:
            contact = contacts[0]
        contact._server_property_changed("client-capabilities", client_id)

        self.participants[account] = contact
        self.emit("user-joined", contact)

    def _handle_IRO(self, command):
        account = command.arguments[2]
        display_name = urllib.unquote(command.arguments[3])
        client_id = command.arguments[4]
        self.__participant_join(account, display_name, client_id)
        if int(command.arguments[0]) == int(command.arguments[1]):
            self._state = ProtocolState.SYNCHRONIZED

    def _handle_JOI(self, command):
        account = command.arguments[0]
        display_name = urllib.unquote(command.arguments[1])
        client_id = command.arguments[2]
        self.__participant_join(account, display_name, client_id)

    def _handle_BYE(self, command):
        if len(command.arguments) == 1:
            account = command.arguments[0]
            self.emit("user-left", self.participants[passport])
            del self.participants[passport]
        else:
            self._state = ProtocolState.IDLE
            self.participants = {}

    # --------- Messenging ---------------------------------------------------
    def _handle_MSG(self, command):
        self.emit("message-received", IncomingMessage(command))
        
    def _handle_ACK(self, command):
        self.emit("message-delivered", command)

    def _handle_NAK(self, command):
        self.emit("message-undelivered", command)

    # callbacks --------------------------------------------------------------
    def _connect_cb(self, transport):
        self._state = ProtocolState.OPENING
        account = self._conversation._client.profile.account
        if self.__key is not None:
            arguments = (account, self.__session_id, self.__key)
            self._transport.send_command_ex('ANS', arguments)
        else:
            arguments = (account, self.__session_id)
            self._transport.send_command_ex('USR', arguments)
        self._state = ProtocolState.AUTHENTICATING

    def _disconnect_cb(self, transport, reason):
        self._state = ProtocolState.CLOSED


