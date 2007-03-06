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

"""Proxy support for various Clients.

@group Informations: ProxyInfos
@group Interfaces: ProxyfiableClient, AbstractProxy
@group Implementations: HTTPConnectProxy"""

from constants import *
from io import AbstractClient, TCPClient
from parser import HTTPParser

import gobject
import base64
import urlparse

class ProxyInfos(object):
    """Contain informations needed to make use of a proxy.

        @ivar host: hostname of the proxy server.
        @ivar port: port used to connect to server.
        @ivar type: proxy type
        @ivar user: username to use for authentication.
        @ivar password: password to use for authentication.
        @undocumented __get_*, __set_*

        @since: 0.1"""
    
    def __init__(self, host='', port=0, type='http', user=None, password=None):
        """Initializer
            
            @param host: the hostname of the proxy server.
            @type host: string
            
            @param port: the port used to connect to server.
            @type port: integer >= 0 and < 65536

            @param type: proxy type
            @type type: string in ('http', 'https', 'socks4', 'socks5')

            @param user: the username to use for authentication.
            @type user: string
            
            @param password: the password to use for authentication.
            @type password: string"""
        self.host = host
        self.port = port
        self.type = type
        self.user = user
        self.password = password
    
    @staticmethod
    def from_string(url, default_type='http'):
        """Builds a new L{ProxyInfos} instance from a given proxy url string
            @param url: the proxy url string
            @type url: string
            
            @param default_type: the default proxy type
            @type default_type: string in ('http', 'https', 'socks4', 'socks5')

            @return L{ProxyInfos} instance filled with the infos given in the
                url"""
        # scheme://netloc/path;parameters?query#fragment
        # (scheme, netloc, path;parameters, query, fragment)
        url = urlparse.urlsplit(url, default_type)
        proxy_type = url[0]
        location = url[1]
        location = location.rsplit('@',1)
        if len(location) == 1:
            auth = ('','')
            host = location[0]
        else:
            auth = location[0].split(':',1)
            host = location[1]
        host = host.split(':',1)
        if len(host) == 1:
            port = 8080
        else:
            port = int(host[1])
        host = host[0]
        return ProxyInfos(host, port, proxy_type, auth[0], auth[1])

    def __get_port(self):
        return self._port
    def __set_port(self, port):
        self._port = int(port)
        assert(self._port >= 0 and self._port <= 65535)
    port = property(__get_port, __set_port, doc="Port used to connect to server.")

    def __get_type(self):
        return self._type
    def __set_type(self, type):
        assert(type in ('http', 'https', 'socks4', 'socks5'))
        self._type = type
    type = property(__get_type, __set_type, doc="Proxy type.")

    def __str__(self):
        host = '%s:%u' % (self.host, self.port)
        if self.user:
            auth = '%s:%s' % (self.user, self.password)
            host = auth + '@' + host
        return self.type + '://' + host + '/'

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

#class HTTPConnectProxy(AbstractProxy):
#     """HTTP proxy client using the CONNECT method to tunnel the communications.
#        
#        @since: 0.1"""
#    
#    def __init__(self, client, proxy):
#        assert(proxy.type in ('http', 'https'))
#        AbstractProxy.__init__(self, client, proxy)
#
#    def _get_transport(self):
#        if self._transport is None:
#            host = self._proxy.host
#            port = self._proxy.port
#            self._transport = TCPClient(hots, port)
#            self._transport.connect("notify::status", self.__on_status_change)
#            self._transport.connect("error", self.__on_error)
#            self._http_parser = HTTPParser(self._transport)
#            self._http_parser.connect("received", self.__on_received)
#        return self._transport._socket #TODO: a bit ugly :D fix this
#
#    def open(self):
#        """Asks the proxy to open a connection"""
#        if self._status in (IoStatus.OPENING, IoStatus.OPEN):
#            return
#        assert(self._status == IoStatus.CLOSED)
#        socket = self.transport
#        self._transport.open() # FIXME: dirty dirty
#
#    def close(self):
#        """Asks the proxy to close the connection and discard the transport"""
#        self._transport.close()
#
#    def __on_status_change(self,  transport, param):
#        status = transport.get_property("status")
#        if status == IoStatus.OPEN:
#            host = self._client.get_property("host")
#            port = self._client.get_property("port")
#            proxy_protocol  = 'CONNECT %s:%s HTTP/1.1\r\n' % (host, port)
#            proxy_protocol += 'Proxy-Connection: Keep-Alive\r\n'
#            proxy_protocol += 'Pragma: no-cache\r\n'
#            proxy_protocol += 'Host: %s:%s\r\n' % (host, port),
#            proxy_protocol += 'User-Agent: %s/%s\r\n' % (GNet.NAME, GNet.VERSION)
#            if self._proxy.user:
#                auth = base64.encodestring(self._proxy.user + ':' + self._proxy.password)
#                proxy_protocol += 'Proxy-authorization: Basic ' + auth + '\r\n'
#            proxy_protocol += '\r\n'
#            self._transport.send(proxy_protocol)
#        else:
#            self._change_status(status)
#    
#    def __on_received(self, parser, response):
#        if self.get_property("status") == IoStatus.OPENING:
#            if response.status == 200:
#                self._http_parser.delimiter = None
#
#                self._change_status(IoStatus.OPEN)
#            elif response.status == 100:
#                pass
#            elif response.status == 407:
#                self.__on_error(None, IoError.PROXY_AUTHENTICATION_REQUIRED)
#            else:
#                raise NotImplementedError("Unknown Proxy response code")
#
#    def __on_error(self, transport, error_code):
#        if transport is not None and error_code == IoError.CONNECTION_FAILED:
#            error_code = IoError.PROXY_CONNECTION_FAILED
#        self.emit("error", error_code)
#
