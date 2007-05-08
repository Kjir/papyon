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

from base import BaseProtocol
from message import IncomingMessage
import pymsn.profile

import logging
import urllib 
import gobject

__all__ = ['SwitchboardProtocolStatus', 'SwitchboardProtocol']

logger = logging.getLogger('protocol:switchboard')

class NotificationProtocolStatus(object):
    CLOSED = 0
    """Disconnected from the switchboard"""
    OPENING = 1
    """Opening the switchboard"""
    AUTHENTICATING = 3
    """Connected to the switchboard, authenticating"""
    SYNCHRONIZING = 4
    """Authenticated, receiving initial participants"""
    OPEN = 5
    """The switchboard is open, and it is possible to send messages"""
    IDLE = 6
    """Disconnected from the switchboard because of idle status"""


class SwitchboardProtocol(BaseProtocol, gobject.GObject):
    """Protocol used to communicate with the Switchboard Server
        
        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler

        @ivar _status: the current protocol status
        @type _status: integer
        @see L{SwitchboardProtocolStatus}"""
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
                (object,))

    __gproperties__ = {
            "status":  (gobject.TYPE_INT,
                "Status",
                "The status of the communication with the server.",
                0, 4, NotificationProtocolStatus.CLOSED,
                gobject.PARAM_READABLE)
            }

    def __init__(self, client, transport, key, session=None, proxies={}):
        """Initializer

            @param client: the parent instance of L{client.Client}
            @type client: L{client.Client}

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}
            
            @param key: the key used to authenticate to server when connecting
            @type key: string
            
            @param session: the session to join if any
            @type session: string

            @param proxies: a dictonary mapping the proxy type to a
                L{gnet.proxy.ProxyInfos} instance
            @type proxies: {type: string, proxy:L{gnet.proxy.ProxyInfos}}
        """
        BaseProtocol.__init__(self, client, transport, proxies)
        gobject.GObject.__init__(self)
        self.participants = {}
        self.__status = SwitchboardProtocolStatus.CLOSED
    
    # Properties ------------------------------------------------------------
    def __get_status(self):
        return self.__status
    def __set_status(self, status):
        self.__status = status
        self.notify("status")
    status = property(__get_status)
    _status = property(__get_status, __set_status)
        
    def do_get_property(self, pspec):
        if pspec.name == "status":
            return self.__status
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name
    
    # Public API -------------------------------------------------------------
    def invite_user(self, contact):
        """Invite user to join in the conversation
            
            @param contact: the contact to invite
            @type contact: L{profile.Contact}"""
        assert(self.status == SwitchboardProtocolStatus.OPEN)
        self._transport.send_command_ex('CAL', (contact.get_property("passport"),) )

    def send_message(self, message, callback=None, cb_args=()):
        """Send a message to all contacts in this switchboard
        
            @param message: the message to send
            @type message: L{message.OutgoingMessage}"""
        assert(self.status == SwitchboardProtocolStatus.OPEN)
        our_cb_args = (message, callback, cb_args)
        self._transport.send_command(message,
                callback=self.__on_message_sent, cb_args=our_cb_args)

    def __on_message_sent(self, message, user_callback, user_cb_args):
        self.emit("message-sent", message)
        if user_callback:
            user_callback(*user_cb_args)

    def leave_conversation(self):
        """Leave the conversation"""
        assert(self.status == SwitchboardProtocolStatus.OPEN)
        self._transport.send_command_ex('OUT')
    # Handlers ---------------------------------------------------------------
    # --------- Authentication -----------------------------------------------
    def _handle_ANS(self, command):
        if command.arguments[0] == 'OK':
            self._status = SwitchboardStatus.OPEN
        else:
            self._status = SwitchboardStatus.SYNCHRONIZING

    def _handle_USR(self, command):
        self._status(SwitchboardStatus.OPEN)
    
    def _handle_OUT(self, command):
        pass
    # --------- Invitation ---------------------------------------------------
    def __participant_join(self, account, display_name, client_id):
        contacts = self._client.contacts.find_by_account(account)
        if len(contacts) == 0:
            contact = pymsn.profile.Contact(id=0,
                    network_id=pymsn.profile.NetworkID.MSN,
                    account=account,
                    display_name=display_name)
        else:
            contact = contacts[0]
        contact._server_property_changed("client-id", client_id)

        self.participants[account] = contact
        self.emit("user-joined", contact)

    def _handle_IRO(self, command):
        account = command.arguments[2]
        display_name = urllib.unquote(command.arguments[3])
        client_id = command.arguments[4]
        self.__participant_join(account, display_name, client_id)

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
            self._status = SwitchboardProtocolStatus.IDLE
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
        self._status = SwitchboardProtocolStatus.OPENING
        account = self._client.profile.account
        if self.__session is not None:
            arguments = (account, self.__key, self.__session)
            self._transport.send_command_ex('ANS', arguments )
        else:
            arguments = (account, self.__key) 
            self._transport.send_command_ex('USR', arguments)
        self._status = SwitchboardProtocolStatus.AUTHENTICATING

    def _disconnect_cb(self, transport):
        self._status = SwitchboardProtocolStatus.CLOSED


