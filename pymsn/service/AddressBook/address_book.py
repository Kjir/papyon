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
            "memberships":     (gobject.TYPE_INT,
                "Memberships",
                "Membership relation with the contact.",
                0, 15, 0, gobject.PARAM_READABLE)
            }

    def __init__(self, id, network_id, account, display_name):
        """Initializer"""
        gobject.GObject.__init__(self)
        self.id = id
        self.network_id = network_id
        self.account = account
        self.display_name = display_name

        self.memberships = sharing.Membership.UNKNOWN
        self.infos = []

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

    ### gobject properties
    def do_get_property(self, pspec):
        if pspec.name == "memberships":
            return self.memberships
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
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
        gobject.GObject.__init__(self)
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

    def find_by_account(self, account):
        result = []
        for network in (NetworkID.MSN, NetworkID.EXTERNAL):
            key = (network, account)
            if key in self._contacts:
                result.append(self._contacts[key])
        return result

    def find_by_memberships(self, memberships):
        result = []
        for key, contact in self._contacts.iteritems():
            if contact.is_member(memberships):
                result.append(contact)
        return result

    def contacts_by_domain(self, predicate=None):
        result = {}
        for key, contact in self._contacts.iteritems():
            if predicate is not None and not predicate(contact):
                continue
            domain = key[1].split("@", 1)[1]
            if domain not in result:
                result[domain] = []
            result[domain].append(contact)
        return result

    # Properties
    def _get_status(self):
        return self._status
    status = property(_get_status)

    # Callbacks
    def _ab_find_all_cb(self, soap_response, contacts):
        self.__ab_find_all_response = contacts
        if self.__find_membership_response is not None:
            self.__build_addressbook()

    def _find_membership_cb(self, soap_response, members):
        self.__find_membership_response = members
        if self.__ab_find_all_response is not None:
            self.__build_addressbook()

    ### gobject properties
    def do_get_property(self, pspec):
        if pspec.name == "status":
            return self._status
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name

    # Private
    def __build_addressbook(self):
        for contact in self.__ab_find_all_response:
            if contact.type == "Me":
                continue #FIXME: update the profile
            c = Contact(contact.id,
                    contact.netword_id,
                    contact.account,
                    contact.display_name)
            c._add_membership(sharing.Membership.FORWARD)
            self._contacts[(contact.netword_id, contact.account)] = c

        for membership, members in self.__find_membership_response.iteritems():
            if membership == "Allow":
                membership = sharing.Membership.ALLOW
            elif membership == "Block":
                membership = sharing.Membership.BLOCK
            elif membership == "Reverse":
                membership = sharing.Membership.REVERSE
            elif membership == "Pending":
                membership = sharing.Membership.PENDING
            else:
                raise NotImplementedError("Unknown Membership Type : " + membership)
            for member in members:
                key = (member.netword_id, member.account)
                if key in self._contacts:
                    self._contacts[key]._add_membership(membership)
                else:
                    self._contacts[key] = Contact(
                            "00000000-0000-0000-0000-000000000000",
                            member.netword_id,
                            member.account,
                            member.display_name,
                            membership)
        del self.__ab_find_all_response
        del self.__find_membership_response
        self._status = AddressBookStatus.SYNCHRONIZED
        self.notify("status")

gobject.type_register(AddressBook)
