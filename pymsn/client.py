# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

"""Client
This module contains classes that clients should use in order to make use
of the library.

Ideally you would inherit from the L{Client} class and override the
abstract methods."""

from transport import *
import profile
import msnp

import logging

__all__ = ['Client']

logger = logging.getLogger('client')

class Client(object):
    """This class provides way to connect to the notification server as well
    as methods to manage the contact list, and the personnal settings.

    Basically you should inherit from this class and implement the callbacks
    in order to build a client.
    
    @group Connection: login, logout"""

    def __init__(self, server, account, proxies={}):
        """Initializer

            @param server: the Notification server to connect to.
            @type server: tuple(host, port)

            @param account: the account to use for authentication.
            @type account: tuple(account, password)

            @param proxies: proxies that we can use to connect
            @type proxies: {type: string => L{gnet.proxy.ProxyInfos}}"""
        self._account = account
        self._proxies = proxies

        self._transport = DirectConnection(server, ServerType.NOTIFICATION, self._proxies)
        self._protocol = msnp.NotificationProtocol(self, self._transport, self._proxies)
        self.profile = profile.User(self._account, self._protocol)

    ### public methods & properties
    def login(self):
        """Login to the server."""
        self._transport.establish_connection()

    def logout(self):
        """Logout from the server."""
        self._protocol.signoff()

