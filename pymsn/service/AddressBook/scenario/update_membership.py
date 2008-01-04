# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Johann Prieur <johann.prieur@gmail.com>
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
from pymsn.service.AddressBook.scenario.base import BaseScenario
from pymsn.service.AddressBook.constants import *

from pymsn.profile import NetworkID
from pymsn.profile import Membership

__all__ = ['UpdateMembershipScenario']

class UpdateMembershipScenario(BaseScenario):
    """Scenario used to update contact memberships in a safe way
        @undocumented: __membership_mapping, __contact_type"""

    __membership_mapping = { Membership.FORWARD: "Forward",
                             Membership.ALLOW: "Allow",
                             Membership.BLOCK: "Block",
                             Membership.REVERSE: "Reverse",
                             Membership.PENDING: "Pending" }
    
    __contact_type = { NetworkID.MSN: "Passport",
                       NetworkID.EXTERNAL: "Email" }

    def __init__(self, sharing, callback, errback, scenario,
                 account, network, state, old_membership, new_membership):
        """Updates contact memberships.

           @type scenario: L{Scenario<pymsn.service.AddressBook.scenario.base.Scenario>}
           @type network: L{NetworkID<pymsn.profile.NetworkID>}
           @type old_memberships: bitmask of L{Membership<pymsn.profile.Membership>}
           @type new_memberships: bitmask of L{Membership<pymsn.profile.Membership>}
        """
        BaseScenario.__init__(self, scenario, callback, errback)
        self.__sharing = sharing

        self.account = account
        self.contact_type = UpdateMembershipScenario.__contact_type[network]
        self.old = old_membership
        self.new = new_membership
        self.state = state

    def execute(self):
        self.__process_delete([2**p for p in range(5)])

    def __process_delete(self, memberships):
        if memberships == []:
            self.__process_add([2**p for p in range(5)])
            return

        current = memberships.pop()
        if current & (self.old ^ self.new):
            if current & self.old:
                membership = UpdateMembershipScenario.__membership_mapping[current]
                self.__sharing.DeleteMember((self.__process_delete, memberships),
                                            (self.__common_errback,),
                                            self._scenario, membership,
                                            self.contact_type, self.state,
                                            self.account)
        else:
            self.__process_delete(memberships)

    def __process_add(self, memberships):
        if memberships == []:
            callback = self._callback
            callback[0](*callback[1:])
            return
        
        current = memberships.pop()
        if current & (self.old ^ self.new):
            if current & self.new:
                membership = UpdateMembershipScenario.__membership_mapping[current]
                self.__sharing.AddMember((self.__process_add, memberships),
                                         (self.__common_errback,),
                                         self._scenario, membership,
                                         self.contact_type, self.state,
                                         self.account)
        else:
            self.__process_add(memberships)

    def __common_errback(self, error_code):
        # TODO : identify membership error codes
        errcode = AddressBookError.UNKNOWN
        errback = self._errback[0]
        args = self._errback[1:]
        errback(errcode, *args)
