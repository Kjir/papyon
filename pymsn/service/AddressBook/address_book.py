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

    __gsignals__ =  {
        "contact-added": (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        }
    __gproperties__ = {
        "state":  (gobject.TYPE_INT,
            "State",
            "The state of the addressbook.",
            0, 2, AddressBookState.NOT_SYNCHRONIZED,
            gobject.PARAM_READABLE)
        }

    def __init__(self, contacts_security_token, http_proxy=None): #TODO: pass an SSO client instead of the security token
        gobject.GObject.__init__(self)
        self._ab_client = ab.AB(contacts_security_token, http_proxy)
        self._sharing_client = sharing.Sharing(contacts_security_token, http_proxy)
        self.__state = AddressBookState.NOT_SYNCHRONIZED
        self.__ab_find_all_groups_response = None
        self.__ab_find_all_contacts_response = None
        self.__find_membership_response = None

        self.groups = {}
        self.contacts = AddressBookStorage()
        self._profile = None

    def sync(self):
        if self._state != AddressBookState.NOT_SYNCHRONIZED:
            return
        self._state = AddressBookState.SYNCHRONIZING
        self._ab_client.ABFindAll("Initial", False, self._ab_find_all_cb)
        self._sharing_client.FindMembership("Initial", self._find_membership_cb)

    # Manipulation
    def add_contact(self, passport, messenger=True):
        self._ab_client.ABContactAdd("ContactSave", passport, messenger,
                                     "LivePending", self._ab_contact_add_cb)

    def delete_contact(self, contact, messenger_only=False):
        if messenger_only:
            properties = { "displayName":"", "isMessengerUser":"false" }
            self._ab_client.ABContactUpdate("Timer", contact.id(), properties,
                                            self._ab_delete_contact_msgr_cb)
        else:
            self._ab_client.ABContactDelete("Timer", contact.id(),
                                            self._ab_delete_contact_cb)

    def block_contact(self, contact):
        pass

    def unblock_contact(self, contact):
        pass

    def add_group(self, group_name):
        self._ab_client.ABGroupAdd("GroupSave", group_name,
                                   self._ab_add_group_cb)

    def delete_group(self, group):
        self._ab_client.ABGroupDelete("Timer", group.id(),
                                      self._ab_delete_group_cb)

    def change_group_name(self, group, new_name):
        self._ab_client.ABGroupUpdate("GroupSave", group.id(), new_name,
                                      self._ab_change_group_name_cb)

    def add_contact_to_group(self, contact, group):
        self._ab_client.ABGroupContactAdd("GroupSave", group.id(), contact.id(),
                                          self._ab_add_contact_to_group_cb)

    def delete_contact_from_group(self, contact, group):
        self._ab_client.ABGroupDelete("GroupSave", contact.id(), group.id(),
                                      self._ab_delete_contact_from_group_cb)

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

    # Callbacks
    def _ab_find_all_cb(self, soap_response, groups, contacts):
        self.__ab_find_all_groups_response = groups
        self.__ab_find_all_contacts_response = contacts
        if self.__find_membership_response is not None:
            self.__build_addressbook()

    def _find_membership_cb(self, soap_response, members):
        self.__find_membership_response = members
        if self.__ab_find_all_contacts_response is not None:
            self.__build_addressbook()

    def _ab_contact_add_cb(self, soap_response, contact):
        c = profile.Contact(contact.id,
                            contact.network_id,
                            contact.account,
                            contact.display_name)
        self.contacts.add_contact(c)
        self.emit("contact-added", c)

    def _ab_contact_add_find_all_cb(self, soap_response, groups, contacts):
        # find the new contact in contacts and add it
        pass

    def _ab_delete_contact_msgr_cb(self, soap_response):
        pass

    def _ab_delete_contact_cb(self, soap_response):
        pass

    def _ab_add_group_cb(self, soap_response, group_guid):
        pass

    def _ab_delete_group_cb(self, soap_response):
        pass

    def _ab_change_group_name_cb(self, soap_response):
        pass

    def _ab_add_contact_to_group_cb(self, soap_response):
        pass

    def _ab_delete_contact_from_group_cb(self, soap_response):
        pass

    ### gobject properties
    def do_get_property(self, pspec):
        if pspec.name == "state":
            return self._state
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name

    # Private
    def __build_addressbook(self):
        for group in self.__ab_find_all_groups_response:
            g = profile.Group(group.id, group.name)
            self.groups[group.id] = g

        for contact in self.__ab_find_all_contacts_response:
            c = profile.Contact(contact.id,
                                contact.network_id,
                                contact.account,
                                contact.display_name)
            if contact.type == "Me":
                self._profile = c
            else:
                c._add_membership(profile.Membership.FORWARD)
                self.contacts.add_contact(c)

        for membership, members in self.__find_membership_response.iteritems():
            if membership == "Allow":
                membership = profile.Membership.ALLOW
            elif membership == "Block":
                membership = profile.Membership.BLOCK
            elif membership == "Reverse":
                membership = profile.Membership.REVERSE
            elif membership == "Pending":
                membership = profile.Membership.PENDING
            else:
                raise NotImplementedError("Unknown Membership Type : " + membership)
            for member in members:
                key = (member.network_id, member.account)
                result_set = self.contacts\
                        .search_by_account(member.account)\
                        .search_by_network_id(member.network_id)
                if len(result_set) > 0:
                    assert(len(result_set) == 1)
                    for contact in result_set:
                        contact._add_membership(membership)
                else:
                    contact = profile.Contact(
                            "00000000-0000-0000-0000-000000000000",
                            member.network_id,
                            member.account,
                            member.display_name,
                            membership)
                    self.contacts.add_contact(contact)
        del self.__ab_find_all_contacts_response
        del self.__ab_find_all_groups_response
        del self.__find_membership_response
        self._state = AddressBookState.SYNCHRONIZED

gobject.type_register(AddressBook)
