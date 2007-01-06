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

"""Proxy support for various Clients."""

from gnet.constants import *
from gnet.types import ProxyInfos
from gnet.io import AbstractClient, TCPClient
from gnet.parser import HTTPParser

import gobject
import base64

class ProxyfiableClient(object):
    def _setup_transport(self, transport, status):
        self._transport = transport
        self._change_status(status)


class AbstractProxy(AbstractClient):
    def __init__(self, client, proxy_infos):
        self._client = client
        self._proxy = proxy_infos
        AbstractClient.__init__(self, proxy_infos.host, proxy_infos.port)
gobject.type_register(AbstractProxy)


class HTTPConnectProxy(AbstractProxy):
    def open(self):
        """Open the connection."""
        if not self._pre_open():
            return
        host = self._proxy.host
        port = self._proxy.port
        self._transport = TCPClient(hots, port)
        self._transport.connect("notify::status", self.__on_status_change)
        self._transport.connect("error", self.__on_error)
        self._http_parser = HTTPParser(self._transport)
        self._received_signal = \
                self._http_parser.connect("received", self.__on_received)

    def close(self):
        """Close the connection."""
        self._transport.close()

    def send(self, buffer, callback=None, *args):
        self._client.send(buffer, callback, *args)

    def _change_status(self, status):
        AbstractProxy._change_status(self, status)
        self._client._setup_transport(self._transport._transport, status)

    def __on_status_change(self,  transport, param):
        status = transport.get_property("status")
        if status == IoStatus.OPEN:
            host = self._client.get_property("host")
            port = self._client.get_property("port")
            proxy_protocol  = 'CONNECT %s:%s HTTP/1.1\r\n' % (host, port)
            proxy_protocol += 'Proxy-Connection: Keep-Alive\r\n'
            proxy_protocol += 'Pragma: no-cache\r\n'
            proxy_protocol += 'Host: %s:%s\r\n' % (host, port),
            proxy_protocol += 'User-Agent: %s/%s\r\n' % (GNet.NAME, GNet.VERSION)
            if self._proxy.user:
                auth = base64.encodestring(self._proxy.user + ':' + self._proxy.password)
                proxy_protocol += 'Proxy-authorization: Basic ' + auth + '\r\n'
            proxy_protocol += '\r\n'
            self._transport.send(proxy_protocol)
        else:
            self._change_status(status)
    
    def __on_received(self, parser, response):
        if self.get_property("status") == IoStatus.OPENING:
            if response.status == 200:
                self._http_parser.delimiter = None
                self._http_parser.disconnect(self._received_signal)
                del self._received_signal
                del self._http_parser
                self._change_status(IoStatus.OPEN)
            elif response.status == 100:
                pass
            elif response.status == 407:
                self.__on_error(None, IoError.PROXY_AUTHENTICATION_REQUIRED)
            else:
                raise NotImplementedError("Unknown Proxy response code")

    def __on_error(self, transport, error_code):
        if transport is not None and error_code == IoError.CONNECTION_FAILED:
            error_code = IoError.PROXY_CONNECTION_FAILED
        self.emit("error", error_code)

class HTTPConnectProxy(AbstractProxy):
     """HTTP proxy client using the CONNECT method to tunnel the communications.
        
        @since: 0.1"""
    
    def __init__(self, client, proxy):
        assert(proxy.type in ('http', 'https'))
        AbstractProxy.__init__(self, client, proxy)

    def _get_transport(self):
        if self._transport is None:
            host = self._proxy.host
            port = self._proxy.port
            self._transport = TCPClient(hots, port)
            self._transport.connect("notify::status", self.__on_status_change)
            self._transport.connect("error", self.__on_error)
            self._http_parser = HTTPParser(self._transport)
            self._http_parser.connect("received", self.__on_received)
        return self._transport._socket #TODO: a bit ugly :D fix this

    def open(self):
        """Asks the proxy to open a connection"""
        if self._status in (IoStatus.OPENING, IoStatus.OPEN):
            return
        assert(self._status == IoStatus.CLOSED)
        socket = self.transport
        self._transport.open() # FIXME: dirty dirty

    def close(self):
        """Asks the proxy to close the connection and discard the transport"""
        self._transport.close()

    def __on_status_change(self,  transport, param):
        status = transport.get_property("status")
        if status == IoStatus.OPEN:
            host = self._client.get_property("host")
            port = self._client.get_property("port")
            proxy_protocol  = 'CONNECT %s:%s HTTP/1.1\r\n' % (host, port)
            proxy_protocol += 'Proxy-Connection: Keep-Alive\r\n'
            proxy_protocol += 'Pragma: no-cache\r\n'
            proxy_protocol += 'Host: %s:%s\r\n' % (host, port),
            proxy_protocol += 'User-Agent: %s/%s\r\n' % (GNet.NAME, GNet.VERSION)
            if self._proxy.user:
                auth = base64.encodestring(self._proxy.user + ':' + self._proxy.password)
                proxy_protocol += 'Proxy-authorization: Basic ' + auth + '\r\n'
            proxy_protocol += '\r\n'
            self._transport.send(proxy_protocol)
        else:
            self._change_status(status)
    
    def __on_received(self, parser, response):
        if self.get_property("status") == IoStatus.OPENING:
            if response.status == 200:
                self._http_parser.delimiter = None

                self._change_status(IoStatus.OPEN)
            elif response.status == 100:
                pass
            elif response.status == 407:
                self.__on_error(None, IoError.PROXY_AUTHENTICATION_REQUIRED)
            else:
                raise NotImplementedError("Unknown Proxy response code")

    def __on_error(self, transport, error_code):
        if transport is not None and error_code == IoError.CONNECTION_FAILED:
            error_code = IoError.PROXY_CONNECTION_FAILED
        self.emit("error", error_code)

