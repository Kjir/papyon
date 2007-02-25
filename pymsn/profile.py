# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

"""Profile of the User connecting to the service, as well as the profile of
contacts in his/her contact list."""

import gobject

__all__ = ['Presence', 'User', 'Contact']


class ClientCapabilities(object):
    IS_BOT = 0x00020000
    IS_MOBILE_DEVICE = 0x00000001
    IS_MSN_MOBILE = 0x00000040
    IS_MSN_DIRECT_DEVICE = 0x00000080

    IS_MEDIA_CENTER_USER = 0x00002000
    IS_MSN8_USER = 0x00000002

    IS_WEB_CLIENT = 0x00000200
    IS_TGW_CLIENT = 0x00000800

    HAS_SPACE = 0x00001000
    HAS_WEBCAM = 0x00000010
    HAS_ONECARE = 0x01000000

    RENDERS_GIF = 0x00000004
    RENDERS_ISF = 0x00000008

    SUPPORTS_CHUNKING = 0x00000020
    SUPPORTS_DIRECT_IM = 0x00004000
    SUPPORTS_WINKS = 0x00008000
    SUPPORTS_SHARED_SEARCH = 0x00010000
    SUPPORTS_VOICE_IM = 0x00040000
    SUPPORTS_SECURE_CHANNEL = 0x00080000
    SUPPORTS_SIP_INVITE = 0x00100000
    SUPPORTS_SHARED_DRIVE = 0x00400000

    P2P_SUPPORTS_TURN = 0x02000000
    P2P_BOOTSTRAP_VIA_UUN = 0x04000000
    
    def __init__(self, client_id):
        self.client_id = client_id

    def __getattr__(self, name):
        mask = getattr(self, name.upper(), None)
        if mask is None:
            raise AttributeError("object 'ClientCapabilities' has no attribute '%s'" % name)
        else:
            return mask & self.client_id != 0

    def __setattr__(self, name, value):
        mask = getattr(self, name.upper(), None)
        if mask is None:
            raise AttributeError("object 'ClientCapabilities' has no attribute '%s'" % name)
        else:
            if value == True:
                self.client_id |= mask
            else:
                self.client_id ^= mask

    def p2p_aware(self):
        return (self.client_id & 0xf0000000 != 0)


class Presence(object):
    """Presence states.

    The members of this class are used to identify the Presence that a user
    wants to advertise to the contacts on his/her contact list.
        
        @cvar ONLINE: online
        @cvar BUSY: busy
        @cvar IDLE: idle
        @cvar AWAY: away
        @cvar BE_RIGHT_BACK: be right back
        @cvar ON_THE_PHONE: on the phone
        @cvar OUT_TO_LUNCH: out to lunch
        @cvar INVISIBLE: status hidden from contacts
        @cvar OFFLINE: offline"""
    ONLINE = 'NLN'
    BUSY = 'BSY'
    IDLE = 'IDL'
    AWAY = 'AWY'
    BE_RIGHT_BACK = 'BRB'
    ON_THE_PHONE = 'PHN'
    OUT_TO_LUNCH = 'LUN'
    INVISIBLE = 'HDN'
    OFFLINE = 'FLN'


class Membership(object):
    UNKNOWN = 0
    FORWARD = 1
    ALLOW   = 2
    BLOCK   = 4
    REVERSE = 8
    PENDING = 16


class User(gobject.GObject):
    """Profile of the User connecting to the service
    
        @undocumented: do_get_property, do_set_property, __gproperties__
        
        @ivar account: the account name
        @ivar password: the password used to authenticate
        @ivar profile: the profile sent by the server
        @ivar display_name: the display name shown to contacts
        @ivar presence: the presence advertised
        @ivar personal_message: the personal message shown to contacts"""""
    
    __gproperties__ = {
            "display-name": (gobject.TYPE_STRING,
                "Friendly name",
                "A nickname that the user chooses to display to others",
                "",
                gobject.PARAM_READABLE),

            "personal-message": (gobject.TYPE_STRING,
                "Personal message",
                "The personal message that the user wants to display",
                "",
                gobject.PARAM_READABLE),
            
            "profile": (gobject.TYPE_STRING,
                "Profile",
                "the text/x-msmsgsprofile sent by the server",
                "",
                gobject.PARAM_READABLE),

            "presence": (gobject.TYPE_STRING,
                "Presence",
                "The presence to show to others",
                Presence.OFFLINE,
                gobject.PARAM_READABLE),
            }

    def __init__(self, account):
        #self._protocol = ns_protocol
        self._account = account[0]
        self._password = account[1]

        self._profile = ""
        self._display_name = self._account.split("@", 1)[0]
        self._presence = Presence.OFFLINE
        self._personal_message = ""
        #FIXME: Display Picture

    @property
    def account(self):
        return self._account

    @property
    def password(self):
        return self._password

    @property
    def profile(self):
        return self._profile

    def __set_display_name(self, display_name):
        pass #FIXME: set the display name
    def __get_display_name(self):
        return self._display_name
    display_name = property(__get_display_name, __set_display_name)
        
    def __set_presence(self, presence):
        pass #FIXME: set the presence
    def __get_presence(self):
        return self._presence
    presence = property(__get_presence, __set_presence)

    def __set_personal_message(self, personal_message):
        pass #FIXME: set the personal message
    def __get_personal_message(self):
        return self._personal_message
    personal_message = property(__get_personal_message, __set_personal_message)

    def _server_property_changed(self, name, value):
        assert(name in __gproperties__.keys())
        name = name.lower().replace("-", "_")
        setattr(self, name, value)
        self.notify(name)

    def do_get_property(self, pspec):
        name = pspec.name.lower().replace("-", "_")
        return getattr(self, name)


class Contact(gobject.GObject):
    """Contact related information
        @undocumented: do_get_property, do_set_property, __gproperties__"""
    
    __gsignals__ =  {
            "added": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "added-me": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "removed": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "removed-me": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "blocked": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "allowed": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            }

    __gproperties__ = {
            "memberships": (gobject.TYPE_INT,
                "Memberships",
                "Membership relation with the contact.",
                0, 15, 0, gobject.PARAM_READABLE),

            "display-name": (gobject.TYPE_STRING,
                "Friendly name",
                "A nickname that the user chooses to display to others",
                "",
                gobject.PARAM_READWRITE),

            "personal-message": (gobject.TYPE_STRING,
                "Personal message",
                "The personal message that the user wants to display",
                "",
                gobject.PARAM_READABLE),

            "presence": (gobject.TYPE_STRING,
                "Presence",
                "The presence to show to others",
                Presence.OFFLINE,
                gobject.PARAM_READABLE),
            }

    def __init__(self, id, network_id, account, display_name):
        """Initializer"""
        gobject.GObject.__init__(self)
        self._id = id
        self._network_id = network_id
        self._account = account

        self._display_name = display_name
        self._personal_message = Presence.OFFLINE
        self._personal_message = ""

        self._memberships = sharing.Membership.UNKNOWN

    @property
    def id(self):
        """Contact identifier in a GUID form"""
        return self._id

    @property
    def network_id(self):
        """Contact network ID"""
        return self._network_id

    @property
    def account(self):
        """Contact account"""
        return self._account

    @property
    def display_name(self):
        """Contact display name"""
        return self._display_name
    
    @property
    def memberships(self):
        """Contact membership value"""
        return self._memberships
    
    ### membership management
    def is_member(self, membership):
        return self.memberships & membership
    
    def _add_membership(self, membership):
        if not self.is_member(sharing.Membership.REVERSE) and \
                membership == sharing.Membership.REVERSE:
            self.emit("added-me")
        elif not self.is_member(sharing.Membership.FORWARD) and \
                membership == sharing.Membership.FORWARD:
            self.emit("added")

        self.memberships |= membership
        self.notify("memberships")

    def _remove_membership(self, membership):
        """removes the given membership from the contact

            @param membership: the membership to remove
            @type membership: int L{sharing.Membership}"""
        if self.is_member(sharing.Membership.REVERSE) and \
                membership == sharing.Membership.REVERSE:
            self.emit("removed-me")
        elif self.is_member(sharing.Membership.FORWARD) and \
                membership == sharing.Membership.FORWARD:
            self.emit("removed")

        self.memberships ^= membership
        self.notify("memberships")

    def _server_property_changed(self, name, value): #FIXME, should not be used for memberships
        assert(name in __gproperties__.keys())
        name = name.lower().replace("-", "_")
        setattr(self, name, value)
        self.notify(name)

    def do_get_property(self, pspec):
        name = pspec.name.lower().replace("-", "_")
        return getattr(self, name)

gobject.type_register(Contact)

