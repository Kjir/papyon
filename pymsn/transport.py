# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2006  Johann Prieur <johann.prieur@gmail.com>
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

"""Network Transport Layer

This module provides an abstraction of the transport to be used to communicate
with the MSN servers, actually MSN servers can communicate either through direct
connection using TCP/1863 or using TCP/80 by tunelling the protocol inside HTTP
POST requests.

The classes of this module are structured as follow:
G{classtree BaseTransport}"""

import gnet.io
import msnp

import logging
import gobject

__all__=['ServerType', 'BaseTransport', 'DirectConnection']

logger = logging.getLogger('Connection')

class ServerType(object):
    """"""
    SWITCHBOARD = 'SB'
    NOTIFICATION = 'NS'


class BaseTransport(gobject.GObject):
    """Abstract Base Class that modelize a connection to the MSN service, this
    abstraction is used to build various transports that expose the same
    interface, basically a transport is created using its constructor then it
    simply emits signals when network events (or even abstracted network events)
    occur, for example a Transport that successfully connected to the MSN
    service will emit a connection-success signal, and when that transport
    received a meaningful message it would emit a command-received signal.
        
        @ivar server: the server being used to connect to
        @type server: tuple(host, port)
        
        @ivar server_type: the server that we are connecting to, either
            Notification or switchboard.
        @type server_type: L{ServerType}

        @ivar proxies: proxies that we can use to connect
        @type proxies: dict(type => L{gnet.proxy.ProxyInfos})
        
        @ivar transaction_id: the current transaction ID
        @type transaction_id: integer


        @cvar connection-failure: signal emitted when the connection fails
        @type connection-failure: ()

        @cvar connection-success: signal emitted when the connection succeed
        @type connection-success: ()

        @cvar connection-reset: signal emitted when the connection is being
        reset
        @type connection-reset: ()

        @cvar connection-lost: signal emitted when the connection was lost
        @type connection-lost: ()

        @cvar command-received: signal emitted when a command is received
        @type command-received: FIXME

        @cvar command-sent: signal emitted when a command was successfully
            transmitted to the server
        @type command-sent: FIXME

        @undocumented: __gsignals__"""
    
    __gsignals__ = {
            "connection-failure" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "connection-success" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "connection-reset" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "connection-lost" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "command-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "command-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }   

    def __init__(self, server, server_type=ServerType.NOTIFICATION, proxies={}):
        """Connection initialization
        
            @param server: the server to connect to.
            @type server: (host: string, port: integer)

            @param server_type: the server that we are connecting to, either
                Notification or switchboard.
            @type server_type: L{ServerType}

            @param proxies: proxies that we can use to connect
            @type proxies: {type: string => L{gnet.network.ProxyInfos}}"""
        gobject.GObject.__init__(self)
        self.server = server
        self.server_type = server_type
        self.proxies = proxies
        self._transaction_id = 0
    
    def __get_transaction_id(self):
        return self._transaction_id
    transaction_id = property(__get_transaction_id)

    # Connection
    def establish_connection(self):
        """Connect to the server server"""
        raise NotImplementedError

    def lose_connection(self):
        """Disconnect from the server"""
        raise NotImplementedError

    def reset_connection(self, server=None):
        """Reset the connection

            @param server: when set, reset the connection and
                connect to this new server
            @type server: tuple(host, port)"""
        raise NotImplementedError

    # Command Sending
    def send_command(self, command, increment=True, callback=None, *cb_args):
        """
        Sends a L{msnp.Command} to the server.

            @param command: command to send
            @type command: L{msnp.Command}

            @param increment: if False, the transaction ID is not incremented
            @type increment: bool

            @param callback: callback to be used when the command has been
                transmitted
            @type callback: callable

            @param cb_args: callback arguments
            @type cb_args: Any, ...
        """
        raise NotImplementedError

    def send_command_ex(self, command, arguments=None, payload=None, 
            increment=True, callback=None, *cb_args):
        """
        Builds a command object then send it to the server.
        
            @param command: the command name, must be a 3 letters
                uppercase string.
            @type command: string
        
            @param arguments: command arguments
            @type arguments: (string, ...)
        
            @param payload: payload data
            @type payload: string

            @param increment: if False, the transaction ID is not incremented
            @type increment: bool

            @param callback: callback to be used when the command has been
                transmitted
            @type callback: callable

            @param cb_args: callback arguments
            @type cb_args: tuple
        """
        cmd = msnp.Command()
        cmd.build(command, self._transaction_id, payload, *arguments)
        self.send_command(cmd, increment, callback, *cb_args)

    def _increment_transaction_id(self):
        """Increments the Transaction ID then return it.
            
            @rtype: integer"""
        self._transaction_id += 1
        return self._transaction_id
gobject.type_register(BaseTransport)


class DirectConnection(BaseTransport):
    """Implements a direct connection to the net using TCP/1863""" 

    def __init__(self, server, server_type=ServerType.NOTIFICATION, proxies={}):
        BaseTransport.__init__(self, server, server_type, proxies)
        
        transport = gnet.io.TCPClient(server[0], server[1])
        transport.connect("notify::status", self.__on_status_change)
        transport.connect("error", lambda t, msg: self.emit("connection-failure"))

        receiver = gnet.parser.DelimiterParser(transport)
        receiver.connect("received", self.__on_received)

        self._receiver = receiver
        self._receiver.delimiter = "\r\n"
        self._transport = transport
        self.__pending_chunk = None
        self.__resetting = False
        
    __init__.__doc__ = BaseTransport.__init__.__doc__

    ### public commands
    
    def establish_connection(self):
        logger.debug('<-> Connecting to %s:%d' % self.server )
        self._transport.open()

    def lose_connection(self):
        self._transport.close()

    def reset_connection(self, server=None):
        if server:
            self._transport.set_property("host", server[0])
            self._transport.set_property("port", server[1])
            self.server = server
        self.__resetting = True
        self._transport.close()
        self._transport.open()

    def send_command(self, command, increment=True, callback=None, *cb_args):
        logger.debug('>>> ' + repr(command))
        our_cb_args = (command, callback, cb_args)
        self._transport.send(str(command), self.__on_command_sent, *our_cb_args)
        if increment:
            self._increment_transaction_id()

    def __on_command_sent(self, command, user_callback, user_cb_args):
        self.emit("command-sent", command)
        if user_callback:
            user_callback(*user_cb_args)

    ### callbacks
    def __on_status_change(self, transport, param):
        status = transport.get_property("status")
        if status == gnet.constants.IoStatus.OPEN:
            if self.__resetting:
                self.emit("connection-reset")
                self.__resetting = False
            self.emit("connection-success")
        elif status == gnet.constants.IoStatus.CLOSED:
            if not self.__resetting:
                self.emit("connection-lost")

    def __on_received(self, receiver, chunk):
        cmd = msnp.Command()
        if self.__pending_chunk:
            chunk = self.__pending_chunk + "\r\n" + chunk
            cmd.parse(chunk)
            self.__pending_chunk = None
            self._receiver.delimiter = "\r\n"
        else:
            cmd.parse(chunk)
            if cmd.name in msnp.Command.INCOMING_PAYLOAD:
                payload_len = int(cmd.arguments[-1])
                if payload_len > 0:
                    self.__pending_chunk = chunk
                    self._receiver.delimiter = payload_len
                    return
        logger.debug('<<< ' + repr(cmd))
        self.emit("command-received", cmd)
gobject.type_register(DirectConnection)
