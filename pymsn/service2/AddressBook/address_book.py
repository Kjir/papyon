# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
# Copyright (C) 2007 Ole André Vadla Ravnås <oleavr@gmail.com>
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

import ab
import sharing
import scenario

import pymsn.profile as profile

import gobject

__all__ = ['AddressBookState', 'AddressBook']

class AddressBookStorage(set):
    def __init__(self, initial_set=()):
        set.__init__(self, initial_set)

    def __repr__(self):
        return "AddressBook : %d contact(s)" % len(self)

    def add_contact(self, contact):
        self.add(contact)

    def remove_contact(self, contact):
        self.remove(contact)

    def get_first(self):
        for contact in self:
            return contact
        return None

    def __getattr__(self, name):
        if name.startswith("search_by_"):
            field = name[10:]
            def search_by_func(criteria):
                return self.search_by(field, criteria)
            search_by_func.__name__ = name
            return search_by_func
        elif name.startswith("group_by_"):
            field = name[9:]
            def group_by_func():
                return self.group_by(field)
            group_by_func.__name__ = name
            return group_by_func
        else:
            raise AttributeError, name

    def search_by_memberships(self, memberships):
        result = []
        for contact in self:
            if contact.is_member(memberships):
                result.append(contact)
                # Do not break here, as the account
                # might exist in multiple networks
        return AddressBookStorage(result)

    def search_by(self, field, value):
        result = []
        for contact in self:
            if getattr(contact, field) == value:
                result.append(contact)
                # Do not break here, as the account
                # might exist in multiple networks
        return AddressBookStorage(result)

    def group_by(self, field):
        result = {}
        for contact in self:
            value = getattr(contact, field)
            if value not in result:
                result[value] = AddressBookStorage()
            result[value].add_contact(contact)
        return result

class AddressBookState(object):
    """Addressbook synchronization state.

    An adressbook is said to be synchronized when it
    matches the addressbook stored on the server."""

    NOT_SYNCHRONIZED = 0
    """The addressbook is not synchronized yet"""
    SYNCHRONIZING = 1
    """The addressbook is being synchronized"""
    SYNCHRONIZED = 2
    """The addressbook is already synchornized"""

class AddressBook(gobject.GObject):
    
    __gproperties__ = {
        "state":  (gobject.TYPE_INT,
            "State",
            "The state of the addressbook.",
            0, 2, AddressBookState.NOT_SYNCHRONIZED,
            gobject.PARAM_READABLE)
        }

    def __init__(self, sso, proxies=None):
        """The address book object.
        """
        gobject.GObject.__init__(self)
        self._ab = ab.AB(sso, proxies)
        self._sharing = sharing.Sharing(sso, proxies)

        self.__state = AddressBookState.NOT_SYNCHRONIZED
        
        self.groups = {}
        self.contacts = AddressBookStorage()
        self._profile = None

    def sync(self):
        if self._state != AddressBookState.NOT_SYNCHRONIZED:
            return
        self._state = AddressBookState.SYNCHRONIZING
        
        ab_sync = AddressBookInitialScenario(self._ab,
                                             (self.__ab_sync_callback,),
                                             (self.__ab_sync_arrback,))
        ab_sync.execute()
        ms_sync = MembershipInitialScenario(self._sharing,
                                            (self.__membership_sync_callback,),
                                            (self.__membership_sync_errback,))
        ms_sync.execute()

    # Properties
    def __get_state(self):
        return self.__state
    def __set_state(self, state):
        self.__state = state
        self.notify("state")
    state = property(__get_state)
    _state = property(__get_state, __set_state)

    @property
    def profile(self):
        return self._profile

    # API
    def add_messenger_contact(self, messenger_address):
        pass

    def add_email_contact(self, email_address):
        pass

    def add_mobile_contact(self, phone_number):
        pass

    def delete_contact(self, contact):
        pass

    def block_contact(self, contact):
        pass

    def unblock_contact(self, contact):
        pass

    def add_group(self, name):
        pass

    def delete_group(self, group):
        pass

    def change_group_name(self, group, new_name):
        pass

    def add_contact_to_group(self, group, contact):
        pass

    def delete_contact_from_group(self, group, contact):
        pass

    # Callbacks

    # TODO : build/update the addressbook from the responses
    def _ab_sync_callback(self, groups, contacts, ab):
        pass

    def _ab_sync_errback(self, reason):
        pass

    def _sharing_sync_callback(self, members):
        pass

    def _sharing_sync_errback(self, reason):
        pass

gobject.type_register(AddressBook)
