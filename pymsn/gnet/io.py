# -*- coding: utf-8 -*-
#
# Copyright (C) 2005  Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""Async I/O abstraction layer.

This module provides asynchronous network I/O.

@group Client: AbstractClient, SocketClient, TCPClient"""

from gnet.constants import *
from gnet.types import ProxyInfos
from gnet.parser import DelimiterParser

import gobject
import socket

__all__ = ['AbstractClient', 'SocketClient', 'TCPClient']

class AbstractClient(gobject.GObject):
    """Abstract client base class.
    All network client classes implements this interface.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _change_status
        
        @since: 0.1"""
    
    __gproperties__ = {
            "host": (gobject.TYPE_STRING,
                "Remote Host",
                "The remote host to connect to.",
                "",
                gobject.PARAM_READWRITE),

            "port": (gobject.TYPE_INT,
                "Remote Port",
                "The remote port to connect to.",
                -1, 65535, -1,
                gobject.PARAM_READWRITE),
            
            "proxy": (object,
                "Connection proxy",
                "a L{types.ProxyInfos} instance.",
                gobject.PARAM_READWRITE),
            
            "status": (gobject.TYPE_INT,
                "Connection Status",
                "The status of this connection.",
                0, 3, IoStatus.CLOSED,
                gobject.PARAM_READABLE),
            }
        
    __gsignals__ = {
            "error": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_ULONG,)),

            "received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_STRING, gobject.TYPE_ULONG)),

            "sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_STRING, gobject.TYPE_ULONG)),
            }
    
    def __init__(self, host, port, proxy=None):
        """Initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: a port number to connect to
            @type port: integer > 0 and < 65536

            @param proxy: proxy infos
            @type proxy: L{types.ProxyInfos}
        """
        gobject.GObject.__init__(self)
        
        self._host = host
        self._port = port
        self._proxy = proxy

        self._status = IoStatus.CLOSED

    def _change_status(self, new_status):
        self._status = new_status
        self.notify("status")

    def do_get_property(self, pspec):
        if pspec.name == "host":
            return self._host
        elif pspec.name == "port":
            return self._port
        elif pspec.name == "proxy":
            return self._proxy
        elif pspec.name == "status":
            return self._status
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        if pspec.name == "host":
            self._host = value
        elif pspec.name == "port":
            self._port = value
        elif pspec.name == "proxy":
            self._proxy = value
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def open(self):
        """Open the connection."""
        raise NotImplementedError

    def close(self):
        """Close the connection."""
        raise NotImplementedError

    def send(self, buffer, callback=None, *args):
        """Send data to the server.
        
            @param buffer: data buffer.
            @type buffer: string
            
            @param callback: a callback method that would be called when the
                data is atually sent to the server.
            @type callback: callback
            
            @param args: callback arguments to be passed to the callback.
        """
        raise NotImplementedError
gobject.type_register(AbstractClient)


class SocketClient(AbstractClient):
    """Asynchronous Socket client class.
        
        @note: doesn't support proxy
        @sort: __init__, open, send, close
        @undocumented: do_*, __reset_state, __watch_*, __io_*, __connect_done_handler

        @since: 0.1"""
    
    def __init__(self, host, port, domain=AF_INET, type=SOCK_STREAM):
        """Initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536
            
            @param domain: the communication domain.
            @type domain: integer
            @see socket module

            @param type: the communication semantics
            @type type: integer
            @see socket module"""

        AbstractClient.__init__(self, host, port)
        self._domain = domain
        self._type = type
        self._socket = None
        self.__reset_state()
    
    def __reset_state(self):
        sock = socket.socket(self._domain, self._type)
        sock.setblocking(0)

        channel = gobject.IOChannel(sock.fileno())
        channel.set_flags(channel.get_flags() | gobject.IO_FLAG_NONBLOCK)
        channel.set_encoding(None)
        channel.set_buffered(False)
        
        self._socket = sock
        self.__channel = channel

        self.__source_id = None
        self.__source_condition = 0
        self.__outgoing_queue = []
    
    def open(self):
        if len(self._host) == 0 or self._port < 0 or self._port > 65535:
            raise ValueError("Wrong host or port number : (%s, %d)" % \
                    (self._host, self._port) )
        if self._status in (IoStatus.OPENING, IoStatus.OPEN):
            return
        assert(self._status == IoStatus.CLOSED)
        self._change_status(IoStatus.OPENING)
        try:
            self._socket.connect((self._host, self._port))
        except socket.error, e:
            pass
        self.__watch_set_cond(gobject.IO_PRI |
                gobject.IO_IN | gobject.IO_OUT |
                gobject.IO_HUP | gobject.IO_ERR | gobject.IO_NVAL,
                self.__connect_done_handler)
    open.__doc__ = AbstractClient.open.__doc__

    def close(self):
        if self._status in (IoStatus.CLOSING, IoStatus.CLOSED):
            return
        self._change_status(IoStatus.CLOSING)
        self.__watch_remove()
        self.__channel.close()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self._socket.close()        
        self.__reset_state()
        self._change_status(IoStatus.CLOSED)
    close.__doc__ = AbstractClient.close.__doc__
    
    def send(self, buffer, callback=None, *args):
        assert(self._status == IoStatus.OPEN)
        self.__outgoing_queue.append([buffer, False, callback, args])
        self.__watch_add_cond(gobject.IO_OUT)
    send.__doc__ = AbstractClient.send.__doc__

    ### convenience methods
    def __watch_remove(self):
        if self.__source_id is not None:
            gobject.source_remove(self.__source_id)
            self.__source_id = None
            self.__source_condition = 0

    def __watch_set_cond(self, cond, handler=None):
        self.__watch_remove()
        self.__source_condition = cond
        if handler is None:
            handler = self.__io_channel_handler
        self.__source_id = self.__channel.add_watch(cond, handler)
    
    def __watch_add_cond(self, cond):
        if self.__source_condition & cond:
            return
        self.__source_condition |= cond
        self.__watch_set_cond(self.__source_condition)

    def __watch_remove_cond(self, cond):
        if not self.__source_condition & cond:
            return
        self.__source_condition ^= cond
        self.__watch_set_cond(self.__source_condition)
    
    ### asynchronous callbacks
    def __connect_done_handler(self, chan, cond):
        self.__watch_remove()
        opts = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if opts == 0:
            self.__watch_set_cond(gobject.IO_IN | gobject.IO_PRI |
                               gobject.IO_ERR | gobject.IO_HUP)
            self._change_status(IoStatus.OPEN)
        else:
            self.emit("error", IoError.CONNECTION_FAILED)
            self._change_status(IoStatus.CLOSED)
        return False
    
    def __io_channel_handler(self, chan, cond):
        if self._status == IoStatus.CLOSED:
            return False
        # Check for error/EOF
        if cond & (gobject.IO_ERR | gobject.IO_HUP):
            self.close()
            return False
        # Incoming
        if cond & (gobject.IO_IN | gobject.IO_PRI):
            buf = self.__channel.read()
            if buf == "":
                self.close()
                return False
            self.emit("received", buf, len(buf))
        # Outgoing
        if cond & gobject.IO_OUT:            
            item = self.__outgoing_queue[0]
            if item[1]: # sent item
                self.emit("sent", item[0], len(item[0]))
                del self.__outgoing_queue[0]
                if item[2]: # callback
                    item[2](*item[3])
            if len(self.__outgoing_queue) > 0: # send next item
                item = self.__outgoing_queue[0]
                self.__channel.write(item[0])
                item[1] = True
            else:
                self.__watch_remove_cond(gobject.IO_OUT)
        return True
gobject.type_register(SocketClient)


class TCPClient(SocketClient):
    """Asynchronous TCP client class.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, __reset_state, __watch_*, __io_*, __connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port):
        """initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536"""
        SocketClient.__init__(self, host, port, AF_INET, SOCK_STREAM)
gobject.type_register(TCPClient)


class _HTTPConnectClient(AbstractClient):
    """HTTP CONNECT based client.
        
        @undocumented: do_*, __reset_state, __on_*

        @since: 0.1"""

    _PROXY_TYPES = ('http', 'https')
    
    def __init__(self, host, port, proxy):
        assert(proxy.type in self._PROXY_TYPES)
        AbstractClient.__init__(self, host, port, proxy)
        self._transport = TCPClient(proxy.host, proxy.port)
        self._transport.connect("notify::status", self.__on_status_change)
        self._transport.connect("sent", self.__on_sent)
        self._transport.connect("error", self.__on_error)

        self._input_parser = DelimiterParser(self._transport)
        self._input_parser.connect("received", self.__on_received)
        self.__reset_state()
    __init__.__doc__ = AbstractClient.__init__.__doc__
        
    def __reset_state(self):
        self._input_parser.delimiter = "\r\n\r\n"
        self._status = IoStatus.CLOSED

    def open(self):
        self._transport.open()
    open.__doc__ = AbstractClient.open.__doc__

    def close(self):
        self._transport.close()
    close.__doc__ = AbstractClient.close.__doc__

    def send(self, buf, callback=None, cb_args=()):
        assert(self._status == STATUS_OPEN)
        self._transport.send(buf, callback, cb_args)
    send.__doc__ = AbstractClient.send.__doc__

    def __on_status_change(self,  transport, param):
        status = transport.get_property("status")
        if status == STATUS_OPEN:
            proxy_protocol  = 'CONNECT %s:%s HTTP/1.0\r\n' % (self._host, self._port)
            proxy_protocol += 'Proxy-Connection: Keep-Alive\r\n'
            proxy_protocol += 'Pragma: no-cache\r\n'
            proxy_protocol += 'Host: %s:%s\r\n' % (self._host, self._port),
            proxy_protocol += 'User-Agent: %s/%s\r\n' % (GNet.NAME, GNet.VERSION)
            if self._proxy.user:
                auth = base64.encodestring(self._proxy.user + ':' + self._proxy.password)
                proxy_protocol += 'Proxy-authorization: Basic ' + auth + '\r\n'
            proxy_protocol += '\r\n'            
            self._transport.send(proxy_protocol)
        else:
            self._change_status(status)
            
    def __on_sent(self, transport, data, length):
        if self.get_property("status") == STATUS_OPEN:
            self.emit("sent", data, length)
    
    def __on_received(self, receiver, chunk):
        if self.get_property("status") == STATUS_OPENING:
            response_code = chunk.split(' ')[1]
            if response_code == "200":
                self._receiver.delimiter = None
                self._change_status(STATUS_OPEN)
            elif response_code == "100":
                pass
            elif response_code == "407":
                self.__on_error(None, PROXY_AUTHENTICATION_REQUIRED)
            else:
                raise NotImplementedError("Unknown Proxy response code")
        else:
            self.emit("received", chunk)

    def __on_error(self, transport, error_code):
        if transport is not None and error_code == IoError.CONNECTION_FAILED:
            error_code = IoError.PROXY_CONNECTION_FAILED
        self.emit("error", error_code)
#gobject.type_register(HTTPConnectClient)
