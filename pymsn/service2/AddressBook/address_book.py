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

import pymsn.service2.AddressBook.ab as ab
import pymsn.service2.AddressBook.sharing as sharing
import pymsn.service2.AddressBook.scenario as scenario

import pymsn.profile as profile

import gobject

__all__ = ['AddressBookState', 'AddressBook']

class AddressBookStorage(set):
    def __init__(self, initial_set=()):
        set.__init__(self, initial_set)

    def __repr__(self):
        return "AddressBook : %d contact(s)" % len(self)

    def add(self, contact):
        self.add(contact)

    def remove(self, contact):
        self.remove(contact)

    def __getitem__(self, key):
        i = 0
        for contact in self:
            if i == key:
                return key
            i += 1
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
            result[value].add(contact)
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
    
    __gsignals__ = {
            "messenger-contact-added" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "email-contact-added"     : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "mobile-contact-added"    : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "contact-deleted"         : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE, ()),
            "contact-blocked"         : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "contact-unblocked"       : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "group-added"             : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "group-deleted"           : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "group-renamed"           : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "group-contact-added"     : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object)),
            "group-contact-deleted"   : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object))
            }

    __gproperties__ = {
        "state":  (gobject.TYPE_INT,
                   "State",
                   "The state of the addressbook.",
                   0, 2, AddressBookState.NOT_SYNCHRONIZED,
                   gobject.PARAM_READABLE)
        }

    def __init__(self, sso, proxies=None):
        """The address book object."""
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
        
        initial_sync = scenario.InitialSyncScenario(self._ab, self._sharing,
                (self.__initial_sync_callback,),
                (self.__common_errback,))
        initial_sync()

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

    # Public API
    def add_messenger_contact(self, account):
        am = MessengerContactAddScenario(self._ab,
                (self.__add_messenger_contact_cb,),
                (self.__common_errback,))
        am.account = account
        am()

    def add_email_contact(self, email_address):
        ae = EmailContactAddScenario(self._ab,
                (self.__add_email_contact_cb,),
                (self.__common_errback,))
        ae.email_address = email_address
        ae()

    def add_mobile_contact(self, phone_number):
        am = MobileContactAddScenario(self._ab,
                (self.__add_mobile_contact_cb,),
                (self.__common_errback,))
        am.phone_number = phone_number
        am()

    def delete_contact(self, contact):
        dc = ContactDeleteScenario(self._ab,
                (self.__common_callback, 'contact-deleted', contact),
                (self.__common_errback,))
        # dc.contact_guid = contact.guid
        dc()

    def block_contact(self, contact):
        bc = BlockContactScenario(self._sharing,
                (self.__common_callback, 'contact-blocked', contact),
                (self.__common_errback,))
        # bc.type = contact.type
        # bc.account = contact.account
        # bc.state = contact.state
        bc()

    def unblock_contact_cb(self, contact):
        uc = UnblockContactScenario(self._sharing,
                (self.__common_callback, 'contact-unblocked', contact),
                (self.__common_errback,))
        # uc.type = contact.type
        # uc.membership_id = contact.membership_id
        # uc.account = contact.account
        # uc.state = contact.state
        uc()

    def add_group(self, group_name):
        ag = GroupAddScenario(self._ab,
                (self.__add_group_cb,),
                (self.__common_errback,))
        ag.group_name = group_name
        ag()

    def delete_group(self, group):
        dg = GroupDeleteScenario(self._ab,
                (self.__common_callback, 'group-deleted', group),
                (self.__common_errback,))
        # dg.group_guid = group.guid
        dg()


    def rename_group(self, group, new_name):
        rg = GroupRenameScenario(self._ab,
                (self.__common_callback, 'group-renamed', group),
                (self.__common_errback,))
        # rg.group_guid = group.guid
        rg.group_name = new_name
        rg()

    def add_contact_to_group(self, group, contact):
        ac = GroupContactAddScenario(self._ab,
                (self.__common_callback, 'group-contact-added', group, contact),
                (self.__common_errback,))
        # ac.group_guid = group.guid
        # ac.contact_guid = contact.guid
        ac()

    def delete_contact_from_group(self, group, contact):
        dc = GroupContactDeleteScenario(self._ab,
                (self.__common_callback, 'group-contact-deleted', group, contact),
                (self.__common_errback,))
        # dc.group_id = group.guid
        # dc.contact_id = contact.guid
        dc()

    # Callbacks
    def __initial_sync_callback(self, address_book, memberships):
        ab = address_book.ab
        contacts = address_book.contacts
        groups = address_book.groups

        for group in groups:
            g = profile.Group(group.Id, group.Name)
            self.groups[group.Id] = g

        for contact in contacts:
            if not contact.IsMessengerUser:
                #FIXME: maybe we want to avoid filtering
                continue
            try:
                display_name = contact.DisplayName
            except AttributeError:
                display_name = contact.QuickName

            c = profile.Contact(contact.Id,
                    profile.NetworkID.MSN,
                    contact.Account,
                    display_name,
                    profile.Membership.FORWARD)
            c._server_contact_attribute_changed("im_contact",
                    contact.IsMessengerUser)
            
            if contact.Type == "Me":
                self._profile = c
            else:
                self.contacts.add(c)

        for membership, members in memberships.iteritems():
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

            for member in memebers:
                if member.Type != "Passport":
                    #FIXME: maybe we want to avoid filtering
                    continue
                
                contact = self.contacts\
                        .search_by_account(self.member.Account)[0]
                if contact is not None:
                    contact._add_membership(membership)
        self._state = AddressBookState.SYNCHRONIZED

    def __add_messenger_contact_cb(self):
        # TODO : build the contact object
        self.emit('messenger-contact-added')

    def __add_email_contact_cb(self):
        # TODO : build the contact object
        self.emit('email-contact-added')

    def __add_mobile_contact_cb(self):
        # TODO : build the group object
        self.emit('mobile-contact-added')

    def __add_group_cb(self):
        # TODO : build the group object
        self.emit('group-added')

    def __common_callback(self, signal, *args):
        self.emit(signal, *args)

    def __common_errback(self, *args):
        pass

gobject.type_register(AddressBook)
