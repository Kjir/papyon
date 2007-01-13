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

"""Protocol
Protocol abstraction module

This module tries to abstract the msn protocol as much as possible so that we
can easily upgrade or change the protocol easily without disturbing the whole
library.
"""

class NotificationProtocol(gobject.GObject):
    """NotificationProtocol
    Notification protocol absraction.
    
        @undocumented: do_get_property, do_set_property
        @group Informations: set_personal_message, set_friendly_name, set_presence
        @group Contacts: *_contact
        @group Tags: *_tag"""

    __gsignals__ = {
            "login-failure" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "login-success" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            }

    def __init__(self, client, transport, profile, proxies={}):
        """Initializer

            @param client: the parent instance of L{client.Client}
            @type client: L{client.Client}

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}
            
            @param profile: a L{client.UserProfile} instance
            @type profile: L{client.UserProfile}
            @param proxies: a dictonary mapping the proxy type to a
                gio.network.ProxyInfos instance
            @type proxies: {type: string, proxy:L{gio.network.ProxyInfos}}
        """
        gobject.GObject.__init__(self)
        transport.connect("command-received", self.__dispatch_command )
        transport.connect("connection-success", self.__connect_cb)
        transport.connect("connection-failure", self.__disconnect_cb)
        transport.connect("connection-lost", self.__disconnect_cb)
gobject.type_register(NotificationProtocol)


