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

class BlockContactScenario(BaseScenario):
    def __init__(self, sharing, callback, errback, type='',
                 membership_id='', account='', state='Accepted'):
        """Blocks a contact.

            @param sharing: the membership service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param type: 'Passport' | 'Email'
        """
        BaseScenario.__init__(self, 'BlockUnblock', callback, errback)
        self.__sharing = sharing
        
        self.type = type
        self.membership_id = membership_id
        self.account = account
        self.state = state

    def execute(self):
        self.__sharing.DeleteMember((self.__delete_member_callback,),
                                    (self.__delete_member_errback,),
                                    self._scenario, 'Allow', self.type, 
                                    self.state, self.membership_id, None)

    def __delete_member_callback(self):
        self.__sharing.AddMember((self.__add_member_callback,),
                                 (self.__add_member_errback,),
                                 self._scenario, 'Block', self.type, 
                                 self.state, self.account)

    def __delete_member_errback(self):
        errback, args = self.__errback
        errback(*args)
    
    def __add_member_callback(self):
        callback, args = self._callback
        callback(*args)

    def __add_member_errback(self):
        errback, args = self.__errback
        errback(*args)
