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

class MembershipInitialScenario(BaseScenario):
    def __init__(self, membership, callback, errback):
        """Synchronizes the membership content when logging in.

            @param membership: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)            
        """
        BaseScenario.__init__(self, 'Initial', callback, errback)
        self.__membership = membership

    def execute(self):
        self.__membership.FindMembership((self.__membership_findall_callback,),
                                         (self.__membership_findall_errback,),
                                         self._scenario, ['Messenger', 'Invitation']
                                         False, '')

    def __membership_findall_callback(self, result):
        callback, args = self.__callback
        callback(result, *args)

    def __membership_findall_errback(self, reason):
        errback, args = self.__errback
        errback(reason, *args)    
