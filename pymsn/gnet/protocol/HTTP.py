# -*- coding: utf-8 -*-
#
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

from gnet.constants import *
from gnet.types import ProxyInfos
from gnet.io import TCPClient

import gobject
import base64

__all__ = ['HTTP']

class HTTP(gobject.GObject):
    """HTTP protocol client class."""
    
    __gsignals__ = {
            "error" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_ULONG)),

            "response-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "request-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }

    def __init__(self, host, port=80, proxy=None):
        """Connection initialization
        
            @param host: the host to connect to.
            @type host: string

            @param port: the port number to connect to
            @type port: integer

            @param proxy: proxy that we can use to connect
            @type proxy: L{gnet.types.ProxyInfos}"""
        gobject.GObject.__init__(self)
        assert(proxy is None or proxy.type == 'http') # TODO: add support for other proxies (socks4 and 5)
        self._host = host
        self._port = port
        self._proxy = proxy
        self._transport = None
        self._outgoing_queue = []

    def _setup_transport(self):# TODONOW: attach signals
        if self._transport is None:
            if self._proxy is not None:
                self._transport = TCPClient(self._proxy.host, self._proxy.port)
            else:
                self._transport = TCPClient(self._host, self._port)
            self._transport.connect("notify::status", self._on_status_change)
            self._transport.connect("sent", self._on_status_change)
        
        if self._transport.get_property("status") != IoStatus.OPEN:
            self._transport.open()

    def request(self, resource='/', headers=None, data='', method='GET'):
        if headers is None:
            headers = {}
        headers['Host'] = self._host + ':' + self._port
        headers['User-Agent'] = GNet.NAME + '/' + GNet.VERSION

        if len(data) > 0:
            headers['Content-Length'] = str(len(data))

        if self._proxy is not None:
            url = 'http://%s:%d%s' % (self._host, self._port, resource)
            if self._proxy.user:
                auth = self._proxy.user + ':' + self._proxy.password
                credentials = base64.encodestring(auth)
                headers['Proxy-Authorization'] = 'Basic ' + credentials
        else:
            url = resource

        request  = "%s %s HTTP/1.1\r\n" % (method, url)
        for header, value in header.iteritems():
            request += "%s: %s\r\n" % (header, value)
        request += "\r\n" + data
        self._outgoing_queue.append(request)



        
