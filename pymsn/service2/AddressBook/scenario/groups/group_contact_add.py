# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
from pymsn.service2.AddressBook.base import BaseScenario

class GroupContactAddScenario(BaseScenario):
    def __init__(self, ab, callback, errback, group_guid='', contact_id=''):
        """Adds a contact to a group.

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param group_guid: the guid of the group
            @param contact_guid: the guid of the contact to add to the group"""
        BaseScenario.__init__(self, 'GroupSave', callback, errback)
        self.__ab = ab

        self.group_guid = group_guid
        self.contact_guid = contact_guid

    def execute(self):
        self.__ab.GroupContactAdd((self.__group_contact_add_callback,),
                                  (self.__group_contact_add_errback,),
                                  self._scenario, self._group_id, 
                                  self._contact_id)

    def __group_contact_add_callback(self):
        callback, args = self._callback
        callback(*args)

    def __group_contact_add_errback(self, reason):
        errback, args = self._errback
        errback(reason, *args)
