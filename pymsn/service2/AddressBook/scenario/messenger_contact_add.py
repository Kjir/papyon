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
from pymsn.service2.description.AB import ContactType

class MessengerContactAddScenario(BaseScenario):
    def __init__(self, ab, callback, errback, account="", 
                 ContactType.LIVE_PENDING, # TODO : determine contact_type via the sharing service
                 contact_info={}, invite_info={}):
        """Adds a messenger contact and updates the address book.

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)"""
        BaseScenario.__init__(self, 'ContactSave', callback, errback)

        self._ab = ab

        self._account = account 
        self._external_network = account.split("@", 1)[1].startswith("yahoo")

        self.contact_type = contact_type
        self.contact_info = contact_info
        self.invite_info = invite_info

    def __set_account(self, account):
        self._account = account
        self._external_network = account.split("@", 1)[1].startswith("yahoo")
    def __get_account(self):
        return self._account
    account = property(__get_account, __set_account,
                             doc="The passport address of the contact to " \
                                 "add. If the given address is a yahoo " \
                                 "address, this scenario will automatically " \
                                 "try to add both the MSN and Yahoo Messenger" \
                                 " accounts")

    def execute(self):
        # TODO : if self._external_network, always try to add as a passport address
        # then as a yahoo messenger account
        contact_info['account'] = self._account
        contact_info['contact_type'] = self.__contact_type
        contact_info['is_messenger_user'] = True
        self._ab.ContactAdd((self.__contact_add_callback,),
                            (self.__contact_add_errback,),
                            self._scenario, 
                            self.contact_info,
                            self.invite_info)
        if self._external_network:
            # TODO : prepare parameters and make a ContactAdd
            pass

    def __contact_add_callback(self, contact_guid):
        # TODO : get the cached lastchanged date to make a delta findall
        # or directly call a sync scenario
        self._ab.FindAll(self.__scenario, True, None,
                          (self.__find_all_callback, contact_guid),
                          (self.__find_all_errback, contact_guid))

    def __contact_add_errback(self, reason):
        # TODO : analyse the reason, and maybe call execute again
        # instead of transmitting it via __errback. For instance, if self.__yahoo
        # then that could mean that not msn passport is associated with that address
        self.__errback(reason)

    def __find_all_callback(self):
        # TODO : complete the contact list in the client, need to access to
        # the local address book storage, not the service..
        pass

    def __find_all_errback(self, reason):
        self.__errback(reason)
