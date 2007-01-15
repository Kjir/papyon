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

from constants import *

import gobject
import socket
import util.OpenSSL as OpenSSL

__all__ = ['AbstractClient', 'SocketClient', 'SSLSocketClient', 'TCPClient',
        'SSLTCPClient']

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

    def _change_status(self, new_status):
        self._status = new_status
        self.notify("status")

    def _pre_open(self):
        if len(self._host) == 0 or self._port < 0 or self._port > 65535:
            raise ValueError("Wrong host or port number : (%s, %d)" % \
                    (self._host, self._port) )
        if self._status in (IoStatus.OPENING, IoStatus.OPEN):
            return False
        assert(self._status == IoStatus.CLOSED)
        self._change_status(IoStatus.OPENING)
        return True

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
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _reset_state, _watch_*, __io_*, _connect_done_handler

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
        self._reset_state()
    
    def _reset_state(self):
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
    
    def open(self):
        if not self._pre_open():
            return
        try:
            self._transport.connect((self._host, self._port))
        except socket.error, e:
            pass
        self._watch_set_cond(gobject.IO_PRI |
                gobject.IO_IN | gobject.IO_OUT |
                gobject.IO_HUP | gobject.IO_ERR | gobject.IO_NVAL,
                self._connect_done_handler)
    open.__doc__ = AbstractClient.open.__doc__

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
        self._reset_state()
        self._change_status(IoStatus.CLOSED)
    close.__doc__ = AbstractClient.close.__doc__
    
    def send(self, buffer, callback=None, *args):
        assert(self._status == IoStatus.OPEN)
        self._outgoing_queue.append([buffer, 0, callback, args])
        self._watch_add_cond(gobject.IO_OUT)
    send.__doc__ = AbstractClient.send.__doc__

    ### convenience methods
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
    
    ### asynchronous callbacks
    def _connect_done_handler(self, chan, cond):
        self._watch_remove()
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
        # Incoming
        if cond & (gobject.IO_IN | gobject.IO_PRI):
            buf = self._channel.read()
            if buf == "":
                self.close()
                return False
            self.emit("received", buf, len(buf))
        # Outgoing
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
        @undocumented: do_*, _reset_state, _watch_*, __io_*, _connect_done_handler

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

    def __del__(self):
        self.close()

    def _reset_state(self):
        SocketClient._reset_state(self)
        context = OpenSSL.ssl_ctx_new(OpenSSL.sslv3_method())
        #OpenSSL.ssl_ctx_set_default_verify_paths(context)
        #OpenSSL.ssl_ctx_load_verify_locations(context, ca_cert, ca_directory)
        OpenSSL.ssl_ctx_set_verify(context, OpenSSL.SSL_VERIFY_NONE,
                OpenSSL.Callback.ssl_verify_callback_allow_unknown_ca)

        self._ssl_context = context
        self._ssl_socket = OpenSSL.ssl_new(self._ssl_context)
        OpenSSL.ssl_set_connect_state(self._ssl_socket)
        OpenSSL.ssl_set_fd(self._ssl_socket, self._transport.fileno())
        OpenSSL.ssl_set_mode(self._ssl_socket,
                OpenSSL.SSL_MODE_ENABLE_PARTIAL_WRITE)

    def close(self):
        if self._status in (IoStatus.CLOSING, IoStatus.CLOSED):
            return
        self._change_status(IoStatus.CLOSING)
        self._watch_remove()
        self._channel.close()
        try:
            self._transport.shutdown(socket.SHUT_RDWR)
            OpenSSL.ssl_free(self._ssl_socket)
            OpenSSL.ssl_ctx_free(self._ssl_context)
        except:
            pass
        self._reset_state()
        self._change_status(IoStatus.CLOSED)
    close.__doc__ = SocketClient.close.__doc__
    
    ### asynchronous callbacks
    def _connect_done_handler(self, chan, cond):
        # underlying socket is connected, now connect the SSL transport
        self._watch_remove()
        opts = self._transport.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if opts == 0:
            self._watch_set_cond(gobject.IO_IN | gobject.IO_OUT |
                    gobject.IO_PRI | gobject.IO_ERR | gobject.IO_HUP)
            if OpenSSL.ssl_connect(self._ssl_socket) == 1:
                self._change_status(IoStatus.OPEN)
        else:
            self.emit("error", IoError.CONNECTION_FAILED)
            self._change_status(IoStatus.CLOSED)
        return False
    
    def _io_channel_handler(self, chan, cond):
        if self._status == IoStatus.OPENING: # Handshaking
            ret = OpenSSL.ssl_do_handshake(self._ssl_socket)
            err = OpenSSL.ssl_get_error(self._ssl_socket, ret)
            if err == OpenSSL.SSL_ERROR_NONE:
                self._change_status(IoStatus.OPEN)
            elif err in (OpenSSL.SSL_ERROR_WANT_READ,
                    OpenSSL.SSL_ERROR_WANT_WRITE,
                    OpenSSL.SSL_ERROR_WANT_X509_LOOKUP):
                pass
            elif err == OpenSSL.SSL_ERROR_ZERO_RETURN:
                self.emit("error", IoError.SSL_CONNECTION_FAILED)
                self.close()
                return False
            elif err == OpenSSL.SSL_ERROR_SSL:
                self.emit("error", IoError.SSL_PROTOCOL_ERROR)
                self.close()
                return False
            else:
                self.emit("error", IoError.UNKNOWN_ERROR)
                self.close()
                return False
        elif self._status == IoStatus.OPEN:
            if cond & (gobject.IO_ERR | gobject.IO_HUP):
                self.close()
                return False

            if cond & (gobject.IO_IN | gobject.IO_PRI):
                try:
                    buf = OpenSSL.ssl_read(self._ssl_socket, 1024)
                except OpenSSL.SSLError:
                    buf = ""
                if buf is None: # SSL_ERROR_WANT_READ | SSL_ERROR_WANT_WRITE
                    return
                elif buf == "":
                    self.close()
                    return False
                else:
                    self.emit("received", buf, len(buf))
            elif cond & gobject.IO_OUT:
                if len(self._outgoing_queue) > 0: 
                    item = self._outgoing_queue[0]
                    try:
                        ret = OpenSSL.ssl_write(self._ssl_socket, item[0][item[1]:])
                    except OpenSSL.SSLError:
                        self.close()
                        return False
                    if ret >= 0:
                        item[1] += ret
                        if item[1] == len(item[0]):
                            self.emit("sent", item[0], len(item[0]))
                            del self._outgoing_queue[0]
                            if item[2]: # callback
                                item[2](*item[3])
                    else:
                        err = OpenSSL.ssl_get_error(self._ssl_socket, ret)
                        if err == OpenSSL.SSL_ERROR_SSL:
                            self.emit("error", IoError.SSL_PROTOCOL_ERROR)
                        else:
                            self.emit("error", IoError.UNKNOWN_ERROR)
                        self.close()
                        return False
        return True
gobject.type_register(SSLSocketClient)


class TCPClient(SocketClient):
    """Asynchronous TCP client class.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _reset_state, _watch_*, __io_*, _connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port):
        """initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536"""
        SocketClient.__init__(self, host, port, AF_INET, SOCK_STREAM)
gobject.type_register(TCPClient)

class SSLTCPClient(SSLSocketClient):
    """Asynchronous SSL TCP client class.
        
        @sort: __init__, open, send, close
        @undocumented: do_*, _reset_state, _watch_*, __io_*, _connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port):
        """initializer

            @param host: the hostname to connect to.
            @type host: string
            
            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536"""
        SSLSocketClient.__init__(self, host, port, AF_INET, SOCK_STREAM)
gobject.type_register(SSLTCPClient)
