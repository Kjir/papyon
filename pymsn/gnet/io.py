# -*- coding: utf-8 -*-
#
# Copyright (C) 2005  Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2006-2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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

from constants import *

import gobject
import socket
import OpenSSL.SSL as OpenSSL

__all__ = ['SocketClient', 'SSLSocketClient', 'TCPClient', 'SSLTCPClient']


class ProxyfiableClient(object):
    """All proxifiable clients must inherit from this class
    to enable the Proxy object to manipulate them"""

    def __init__(self):
        pass

    def _proxy_opening(self, sock):
        if not self._configure(): return
        self._pre_open()

    def _proxy_open(self):
        self._post_open()

    def _proxy_closed(self):
        self._close()
        


class AbstractClient(gobject.GObject):
    """Abstract client base class.
    All network client classes implements this interface.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _change_status, _configure, _pre_open, _post_open
        
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
    
    def __init__(self, host, port):
        """Initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: a port number to connect to
            @type port: integer > 0 and < 65536
        """
        gobject.GObject.__init__(self)
        self._host = host
        self._port = port
        self._transport = None
        self._status = IoStatus.CLOSED

    def __del__(self):
        self.close()

    def _change_status(self, new_status):
        if self._status != new_status:
            self._status = new_status
            self.notify("status")

    def _configure(self):
        if len(self._host) == 0 or self._port < 0 or self._port > 65535:
            raise ValueError("Wrong host or port number : (%s, %d)" % \
                    (self._host, self._port) )
        if self._status in (IoStatus.OPENING, IoStatus.OPEN):
            return False
        assert(self._status == IoStatus.CLOSED)
        return True

    def _pre_open(self, sock=None):
        if sock is None:
            sock = socket.socket(self._domain, self._type)
        sock.setblocking(0)

        channel = gobject.IOChannel(sock.fileno())
        channel.set_flags(channel.get_flags() | gobject.IO_FLAG_NONBLOCK)
        channel.set_encoding(None)
        channel.set_buffered(False)
        
        self._transport = sock
        self._channel = channel

        self._source_id = None
        self._source_condition = 0
        self._outgoing_queue = []
        self._change_status(IoStatus.OPENING)

    def _post_open(self):
        self._watch_remove()

    # convenience methods
    def _watch_remove(self):
        if self._source_id is not None:
            gobject.source_remove(self._source_id)
            self._source_id = None
            self._source_condition = 0

    def _watch_set_cond(self, cond, handler=None):
        self._watch_remove()
        self._source_condition = cond
        if handler is None:
            handler = self._io_channel_handler
        self._source_id = self._channel.add_watch(cond, handler)
    
    def _watch_add_cond(self, cond):
        if self._source_condition & cond:
            return
        self._source_condition |= cond
        self._watch_set_cond(self._source_condition)

    def _watch_remove_cond(self, cond):
        if not self._source_condition & cond:
            return
        self._source_condition ^= cond
        self._watch_set_cond(self._source_condition)
    
    # public API
    def open(self):
        """Open the connection."""
        if not self._configure():
            return
        try:
            self._pre_open()
            self._transport.connect((self._host, self._port))
        except socket.error, e:
            pass
        self._watch_set_cond(gobject.IO_PRI |
                gobject.IO_IN | gobject.IO_OUT |
                gobject.IO_HUP | gobject.IO_ERR | gobject.IO_NVAL,
                lambda chan, cond: self._post_open())

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
    
    # properties
    def do_get_property(self, pspec):
        if pspec.name == "host":
            return self._host
        elif pspec.name == "port":
            return self._port
        elif pspec.name == "status":
            return self._status
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        if pspec.name == "host":
            self._host = value
        elif pspec.name == "port":
            self._port = value
        else:
            raise AttributeError, "unknown property %s" % pspec.name
gobject.type_register(AbstractClient)


class SocketClient(AbstractClient):
    """Asynchronous Socket client class.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _watch_*, __io_*, _connect_done_handler

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
        
    def close(self):
        if self._status in (IoStatus.CLOSING, IoStatus.CLOSED):
            return
        self._change_status(IoStatus.CLOSING)
        self._watch_remove()
        self._channel.close()
        try:
            self._transport.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self._transport.close()        
        self._change_status(IoStatus.CLOSED)
    close.__doc__ = AbstractClient.close.__doc__
    
    def send(self, buffer, callback=None, *args):
        assert(self._status == IoStatus.OPEN), self._status
        self._outgoing_queue.append([buffer, 0, callback, args])
        self._watch_add_cond(gobject.IO_OUT)
    send.__doc__ = AbstractClient.send.__doc__
    
    def _post_open(self):
        AbstractClient._post_open(self)
        opts = self._transport.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if opts == 0:
            self._watch_set_cond(gobject.IO_IN | gobject.IO_PRI |
                               gobject.IO_ERR | gobject.IO_HUP)
            self._change_status(IoStatus.OPEN)
        else:
            self.emit("error", IoError.CONNECTION_FAILED)
            self._change_status(IoStatus.CLOSED)
        return False
    
    def _io_channel_handler(self, chan, cond):
        if self._status == IoStatus.CLOSED:
            return False

        # Check for error/EOF
        if cond & (gobject.IO_ERR | gobject.IO_HUP):
            self.close()
            return False
        
        if cond & (gobject.IO_IN | gobject.IO_PRI):
            buf = self._channel.read()
            if buf == "":
                self.close()
                return False
            self.emit("received", buf, len(buf))
        
        if cond & gobject.IO_OUT:            
            item = self._outgoing_queue[0]
            if item[1] == len(item[0]): # sent item
                self.emit("sent", item[0], len(item[0]))
                del self._outgoing_queue[0]
                if item[2]: # callback
                    item[2](*item[3])
            if len(self._outgoing_queue) > 0: # send next item
                item = self._outgoing_queue[0]
                item[1] += self._channel.write(item[0][item[1]:])
            else:
                self._watch_remove_cond(gobject.IO_OUT)
        return True
gobject.type_register(SocketClient)


class SSLSocketClient(SocketClient):
    """Asynchronous SSL Socket client class.
        
        @note: doesn't support proxy
        @sort: __init__, open, send, close
        @undocumented: do_*, _watch_*, __io_*, _connect_done_handler

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
        SocketClient.__init__(self, host, port, domain, type)

    def close(self):
        if self._status in (IoStatus.CLOSING, IoStatus.CLOSED):
            return
        self._change_status(IoStatus.CLOSING)
        self._watch_remove()
        self._channel.close()
        try:
            self._transport.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self._change_status(IoStatus.CLOSED)
    close.__doc__ = SocketClient.close.__doc__
    
    def _pre_open(self, sock=None):
        if sock is None:
            sock = socket.socket(self._domain, self._type)
        context = OpenSSL.Context(OpenSSL.SSLv23_METHOD)
        ssl_sock = OpenSSL.Connection(context, sock)
        ssl_sock.set_connect_state()
        ssl_sock.setblocking(False)
        AbstractClient._pre_open(self, ssl_sock)

    def _post_open(self):
        # underlying socket is connected, now connect the SSL transport
        AbstractClient._post_open(self)
        if self._transport.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
            self._watch_set_cond(gobject.IO_IN | gobject.IO_OUT |
                    gobject.IO_PRI | gobject.IO_ERR | gobject.IO_HUP)
        else:
            self.emit("error", IoError.CONNECTION_FAILED)
            self._change_status(IoStatus.CLOSED)
        return False
    
    def _io_channel_handler(self, chan, cond):
        if self._status == IoStatus.OPENING: # Handshaking
            if self._transport.want_read() or self._transport.want_write():
                try:
                    self._transport.do_handshake()
                except OpenSSL.WantX509LookupError:
                    return True
                except (OpenSSL.ZeroReturnError, OpenSSL.SysCallError):
                    self.emit("error", IoError.SSL_CONNECTION_FAILED)
                    self.close()
                    return False
            else:
                self._change_status(IoStatus.OPEN)
        elif self._status == IoStatus.OPEN:
            if cond & (gobject.IO_ERR | gobject.IO_HUP):
                self.close()
                return False

            if cond & (gobject.IO_IN | gobject.IO_PRI):
                try:
                    buf = self._transport.recv(2048)
                except (OpenSSL.WantX509LookupError,
                        OpenSSL.WantReadError, OpenSSL.WantWriteError):
                    return True
                except (OpenSSL.ZeroReturnError, OpenSSL.SysCallError):
                    self.close()
                    return False
                self.emit("received", buf, len(buf))
            elif cond & gobject.IO_OUT:
                print len(self._outgoing_queue)
                if len(self._outgoing_queue) > 0:
                    item = self._outgoing_queue[0]
                    try:
                        ret = self._transport.send(item[0][item[1]:])
                    except (OpenSSL.WantX509LookupError,
                            OpenSSL.WantReadError, OpenSSL.WantWriteError):
                        return True
                    except (OpenSSL.ZeroReturnError, OpenSSL.SysCallError):
                        self.close()
                        return False
                    assert(ret >= 0)
                    self._outgoing_queue[0][1] += ret
                    if self._outgoing_queue[0][1] == len(item[0]):
                        self.emit("sent", item[0], len(item[0]))
                        del self._outgoing_queue[0]
                        if item[2]: # callback
                            item[2](*item[3])
                else:
                    self._watch_remove_cond(gobject.IO_OUT)
        return True
gobject.type_register(SSLSocketClient)


class TCPClient(SocketClient, ProxyfiableClient):
    """Asynchronous TCP client class.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _watch_*, __io_*, _connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port):
        """initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536"""
        SocketClient.__init__(self, host, port, AF_INET, SOCK_STREAM)
        ProxyfiableClient.__init__(self)
gobject.type_register(TCPClient)


class SSLTCPClient(SSLSocketClient, ProxyfiableClient):
    """Asynchronous SSL TCP client class.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _watch_*, __io_*, _connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port):
        """initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536"""
        SSLSocketClient.__init__(self, host, port, AF_INET, SOCK_STREAM)
        ProxyfiableClient.__init__(self)
gobject.type_register(SSLTCPClient)
