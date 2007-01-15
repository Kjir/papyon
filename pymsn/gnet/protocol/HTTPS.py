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
from gnet.io import SSLTCPClient
from gnet.parser import HTTPParser
from gnet.protocol.HTTP import HTTP

__all__ = ['HTTPS']

class HTTPS(HTTP):
    """HTTP protocol client class."""
    def __init__(self, host, port=443, proxy=None):
        """Connection initialization
        
            @param host: the host to connect to.
            @type host: string

            @param port: the port number to connect to
            @type port: integer

            @param proxy: proxy that we can use to connect
            @type proxy: L{gnet.proxy.ProxyInfos}"""
        HTTP.__init__(self, host, port)
        self.__proxy = proxy

    def _setup_transport(self):
        if self._transport is None:
            self._transport = SSLTCPClient(self._host, self._port)
            self._http_parser = HTTPParser(self._transport)
            self._http_parser.connect("received", self._on_response_received)
            self._transport.connect("notify::status", self._on_status_change)
            self._transport.connect("error", self._on_error)
            self._transport.connect("sent", self._on_request_sent)
        
        if self._transport.get_property("status") != IoStatus.OPEN:
            self._transport.open()
