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

__all__ = ['Presence', 'User']


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


class User(gobject.GObject):
    """Profile of the User connecting to the service
    
        @undocumented: do_get_property, do_set_property, __gproperties__
        
        @ivar account: the account name
        @ivar password: the password used to authenticate
        @ivar profile: the profile sent by the server
        @ivar friendly_name: the friendly name shown to contacts
        @ivar presence: the presence advertised
        @ivar personal_message: the personal message shown to contacts"""""
    
    __gproperties__ = {
            "account": (gobject.TYPE_STRING,
                "Account",
                "Account used to connect to the WLM services : steevy.ball@hotmail.com",
                "",
                gobject.PARAM_READABLE),
            
            "password": (gobject.TYPE_STRING,
                "Password",
                "Password user for the account",
                "",
                gobject.PARAM_READABLE),

            "friendly-name":  (gobject.TYPE_STRING,
                "Friendly name",
                "A nickname that the user chooses to display to others",
                "",
                gobject.PARAM_READWRITE),

            "personal-message":  (gobject.TYPE_STRING,
                "Personal message",
                "The personal message that the user wants to display",
                "",
                gobject.PARAM_READWRITE),
            
            "profile": (gobject.TYPE_STRING,
                "Profile",
                "the text/x-msmsgsprofile sent by the server",
                "",
                gobject.PARAM_READWRITE),

            "presence":  (gobject.TYPE_STRING,
                "Presence",
                "The presence to show to others",
                "",
                gobject.PARAM_READWRITE),

            "display-picture":  (gobject.TYPE_STRING,
                "Display picture",
                "The display picture used for this account",
                "",
                gobject.PARAM_READWRITE)
            }

    def __init__(self, ns_protocol, account):
        self._protocol = ns_protocol
        self._account = account[0]
        self._password = account[1]

        self._profile = ""
        self._friendly_name = self._account
        self._presence = Presence.OFFLINE
        self._personal_message = ""
        # FIXME: Display Picture

    def __get_account(self):
        return self._account
    account = property(__get_account)

    def __get_password(self):
        return self._password
    password = property(__get_password)

    def __get_profile(self):
        return self._profile
    profile = property(__get_profile) 

    def __set_friendly_name(self, friendly_name):
        self._protocol.set_friendly_name(friendly_name)
    def __get_friendly_name(self):
        return self._friendly_name
    friendly_name = property(__get_friendly_name, __set_friendly_name)
        
    def __set_presence(self, presence):
        self._protocol.set_presence(presence)
    def __get_presence(self):
        return self._presence
    presence = property(__get_presence, __set_presence)

    def __set_personal_message(self, personal_message):
        self._protocol.set_personal_message(personal_message)
    def __get_personal_message(self):
        return self._personal_message
    personal_message = property(__get_personal_message, __set_personal_message)

    def do_get_property(self, pspec):
        if pspec.name == "account":
            return self._account
        elif pspec.name == "password":
            return self._password
        elif pspec.name == "friendly-name":
            return self._friendly_name
        elif pspec.name == "personal-message":
            return self._personal_message
        elif pspec.name == "presence":
            return self._presence
        elif pspec.name == "profile":
            return self._profile
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        if pspec.name == "friendly-name":
            self._friendly_name = value
        elif pspec.name == "personal-message":
            self._personal_message = value
        elif pspec.name == "presence":
            self._presence = value
        elif pspec.name == "profile":
            self._profile = value
        else:
            raise AttributeError, "unknown property %s" % pspec.name


        

