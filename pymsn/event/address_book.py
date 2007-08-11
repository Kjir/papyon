# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

from base import BaseEventInterface

__all__ = ["AddressBookEventInterface"]

class AddressBookEventInterface(BaseEventInterface):
    def __init__(self, client):
        BaseEventInterface.__init__(self, client)

    def on_addressbook_new_pending_contact(self, pending_contact):
        pass

    def on_addressbook_messenger_contact_added(self, contact):
        pass

    def on_addressbook_messenger_contact_deleted(self, contact):
        pass

    def on_addressbook_messenger_contact_blocked(self, contact):
        pass

    def on_addressbook_messenger_contact_unblocked(self, contact):
        pass

    def on_addressbook_messenger_group_added(self, group):
        pass

    def on_addressbook_messenger_group_deleted(self, group):
        pass

    def on_addressbook_messenger_group_renamed(self, group):
        pass

    def on_addressbook_messenger_group_contact_added(self, group, contact):
        pass

    def on_addressbook_messenger_group_contact_deleted(self, group, contact):
        pass

