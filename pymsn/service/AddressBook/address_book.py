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

import ab
import sharing

import gobject


class Contact(gobject.GObject):
    """Contact related information
        @undocumented: do_get_property, do_set_property"""
    
    __gsignals__ =  {
            "added" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "added-me" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "removed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "removed-me" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "blocked" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "allowed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            }

    __gproperties__ = {
            "membership":     (gobject.TYPE_INT,
                "Memberships",
                "Membership relation with the contact.",
                0, 15, 0, gobject.PARAM_READWRITE)
            }

    def __init__(self, id, type, account, display_name, memberships=sharing.Membership.UNKNOWN):
        """Initializer"""
        gobject.GObject.__init__(self)
        self._id = id
        self._type = type
        self._account = account
        self._display_name = display_name

        self._memberships = memberships
        self._infos = []
    
    ### membership management
    def is_member(self, membership):
        return self._memberships & membership
    
    def _add_membership(self, membership):
        if not self.is_member(sharing.Membership.REVERSE) and \
                membership == sharing.Membership.REVERSE:
            self.emit("added-me")
        elif not self.is_member(sharing.Membership.FORWARD) and \
                membership == sharing.Membership.FORWARD:
            self.emit("added")

        self._memberships |= membership
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

        self._memberships ^= membership
        self.notify("memberships")

    ### gobject properties
    def do_get_property(self, pspec):
        if pspec.name == "lists":
            return self._lists
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        if pspec.name == "lists":
            self._lists = value
        else:
            raise AttributeError, "unknown property %s" % pspec.name


gobject.type_register(Contact)


class AddressBookStatus(object):
    """Addressbook synchronization status.
    
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
        "status":  (gobject.TYPE_INT,
            "Status",
            "The status of the addressbook.",
            0, 2, AddressBookStatus.NOT_SYNCHRONIZED,
            gobject.PARAM_READABLE)
        }

    def __init__(self, contacts_security_token): #TODO: pass an SSO client instead of the security token
        self._ab_client = ab.AB(contacts_security_token)
        self._sharing_client = sharing.Sharing(contacts_security_token)
        self._status = AddressBookStatus.NOT_SYNCHRONIZED
        self.__ab_find_all_response = None
        self.__find_membership_response = None

        self._contacts = {}

    def sync(self):
        if self._status != AddressBookStatus.NOT_SYNCHRONIZED:
            return
        self._status = AddressBookStatus.SYNCHRONIZING
        self.notify("status")
        self._ab_client.ABFindAll(self._ab_find_all_cb)
        self._sharing_client.FindMembership(self._find_membership_cb)

    # Callbacks
    def _ab_find_all_cb(self, soap_response, contacts):
        self.__ab_find_all_response = contacts
        if self.__find_membership_response is not None:
            self.__build_addressbook()

    def _find_membership_cb(self, soap_response, members):
        self.__find_membership_response = members
        if self.__ab_find_all_response is not None:
            self.__build_addressbook()

    # Private
    def __build_addressbook(self):
        for contact in self.__ab_find_all_response:
            if contact.contact_type == "Me":
                continue #FIXME: update the profile
            self._contacts[contact.contact_id] = Contact(contact.contact_id,
                    contact.account_type,
                    contact.account,
                    contact.display_name,
                    sharing.Membership.FORWARD)

gobject.type_register(AddressBook)

