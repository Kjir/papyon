# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2005-2006 Ole André Vadla Ravnås <oleavr@gmail.com> 
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

"""Notification protocol Implementation
Implements the protocol used to communicate with the Notification Server."""

from base import BaseProtocol
from message import IncomingMessage
import pymsn.service.SingleSignOn as SSO
import pymsn.service.AddressBook as AddressBook

import logging
import gobject

__all__ = ['NotificationProtocolStatus', 'NotificationProtocol']

logger = logging.getLogger('protocol')

class ProtocolConstant(object):
    VER = ('MSNP15', 'MSNP14', 'MSNP13', 'CVR0')
    CVR = ('0x0409', 'winnt', '5.1', 'i386', 'MSNMSGR', '8.1.0178', 'msmsgs')
    PRODUCT_ID = "PROD0114ES4Z%Q5W"
    PRODUCT_KEY = "PK}_A_0N_K%O?A9S"


class NotificationProtocolStatus(object):
    CLOSED = 0
    OPENING = 1
    AUTHENTICATING = 2
    SYNCHRONIZING = 3
    OPEN = 4


class NotificationProtocol(BaseProtocol, gobject.GObject):
    """Protocol used to communicate with the Notification Server
        
        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler

        @ivar _status: the current protocol status
        @type _status: integer
        @see L{NotificationProtocolStatus}"""
    __gsignals__ = {
            "mail-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
            }

    __gproperties__ = {
            "status":  (gobject.TYPE_INT,
                "Status",
                "The status of the communication with the server.",
                0, 4, NotificationProtocolStatus.CLOSED,
                gobject.PARAM_READABLE)
            }

    def __init__(self, client, transport, proxies={}):
        """Initializer

            @param client: the parent instance of L{client.Client}
            @type client: L{client.Client}

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}
            
            @param proxies: a dictonary mapping the proxy type to a
                L{gnet.proxy.ProxyInfos} instance
            @type proxies: {type: string, proxy:L{gnet.proxy.ProxyInfos}}
        """
        BaseProtocol.__init__(self, client, transport, proxies)
        gobject.GObject.__init__(self)
        self._status = NotificationProtocolStatus.CLOSED
        self._address_book = None
        self._protocol_version = 0
        
    def do_get_property(self, pspec):
        if pspec.name == "status":
            return self._status
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name
    
    # Handlers ---------------------------------------------------------------
    # --------- Connection ---------------------------------------------------
    def _handle_VER(self, command):
        assert(len(command.arguments) > 1), "Invalid VER response : " + str(command)
        self._protocol_version = int(command.arguments[0].lstrip('MSNP'))
        self._transport.send_command_ex('CVR',
                ProtocolConstant.CVR + (self._client.profile.account,))

    def _handle_CVR(self, command):
        if self._protocol_version >= 15:
            method = 'SSO'
        else:
            method = 'TWN'
        self._status = NotificationProtocolStatus.AUTHENTICATING
        self.notify("status")
        self._transport.send_command_ex('USR',
                (method, 'I', self._client.profile.account))

    def _handle_XFR(self, command):
        if command.arguments[0] == 'NS':
            try:
                host, port = command.arguments[1].split(":", 1)
                port = int(port)
            except ValueError:
                host = command.arguments[1]
                port = self._transport.server[1]
            logger.debug("<-> Redirecting to " + command.arguments[1])
            self._transport.reset_connection((host,port))
        else: # connect to a switchboard
            raise NotImplementedError("Missing Implementation, please fix")

    def _handle_USR(self, command):
        args_len = len(command.arguments)
        
        # MSNP15 have only 4 params for final USR
        assert(args_len == 3 or args_len == 4), "Received USR with invalid number of params : " + str(command)

        if command.arguments[0] == "OK":
            #raise NotImplementedError("Missing Implementation, please fix")
            pass

        # we need to authenticate with a passport server
        elif command.arguments[1] == "S":
            account = self._client.profile.account
            password = self._client.profile.password
            
            if command.arguments[0] == "SSO":
                sso = SSO.SingleSignOn(account, password)
                sso.RequestMultipleSecurityTokens(self._sso_cb, (command.arguments[3],),
                        SSO.LiveService.MESSENGER_CLEAR, SSO.LiveService.CONTACTS)
            elif command.arguments[0] == "TWN":
                raise NotImplementedError, "Missing Implementation, please fix"

    def _handle_SBS(self, command): # unknown command
        pass

    def _handle_OUT(self, command):
        raise NotImplementedError, "Missing Implementation, please fix"

    # --------- Contact List -------------------------------------------------
    def _handle_ADL(self, command):
        if command.arguments[0] == "OK":
            self._status = NotificationProtocolStatus.OPEN
            self.notify("status")

    # --------- Messages -----------------------------------------------------
    def _handle_MSG(self, command):
        msg = IncomingMessage(command)
        if msg.content_type[0] == 'text/x-msmsgsprofile':
            #self.__profile._profile = command
            #FIXME: use the profile
            
            if self._protocol_version < 15:
                #self._transport.send_command_ex('SYN', ('0', '0'))
                raise NotImplementedError, "Missing Implementation, please fix"
            else:
                self._transport.send_command_ex("BLP", ("BL",)) #FIXME: make this configurable somewhere
                self._status = NotificationProtocolStatus.SYNCHRONIZING
                self.notify("status")
                self._address_book.sync()
        elif msg.content_type[0] in \
                ('text/x-msmsgsinitialemailnotification', \
                 'text/x-msmsgsemailnotification'):
            self.emit("mail-received", msg)

    # callbacks --------------------------------------------------------------
    def _connect_cb(self, transport):
        self._status = NotificationProtocolStatus.OPENING
        self.notify("status")
        self._transport.send_command_ex('VER', ProtocolConstant.VER)

    def _disconnect_cb(self, transport):
        self._status = NotificationProtocolStatus.CLOSED
        self.notify("status")

    def _sso_cb(self, nonce, soap_response, *tokens):
        self.__security_tokens = tokens
        clear_token = None
        blob = None
        for token in tokens:
            if token.service_address == SSO.LiveService.MESSENGER_CLEAR[0]:
                clear_token = token
                blob = token.mbi_crypt(nonce)
            elif token.service_address == SSO.LiveService.CONTACTS[0]:
                self._address_book = AddressBook.AddressBook(token)
                self._address_book.connect("notify::status", self._address_book_cb)
        assert(clear_token is not None and blob is not None)
        self._transport.send_command_ex("USR", ("SSO", "S", clear_token.security_token, blob))

    def _address_book_cb(self, address_book, pspec):
        if address_book.status != AddressBook.AddressBookStatus.SYNCHRONIZED:
            return
        mask = ~(AddressBook.Membership.REVERSE | AddressBook.Membership.PENDING)
        predicate = lambda contact: contact.is_member(mask)
        contacts = address_book.contacts_by_domain(predicate)
        s = '<ml l="1">'
        for domain, contacts in contacts.iteritems():
            s += '<d n="%s">' % domain
            for contact in contacts:
                user = contact.account.split("@", 1)[0]
                lists = contact.memberships & mask
                network_id = contact.network_id
                s += '<c n="%s" l="%d" t="%d"/>' % (user, lists, network_id)
            s += '</d>'
        s += '</ml>'
        self._transport.send_command_ex("ADL", payload=s)
