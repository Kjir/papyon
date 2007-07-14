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
    def __init__(self, ab, callback, errback, passport_name="", 
                 ContactType.LIVE_PENDING, # TODO : determine contact_type via the sharing service
                 contact_info={}, invite_info={}):
        """Adds a messenger contact and updates the address book.

            @param ab: the adress book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)"""
        BaseScenario.__init__(self, 'ContactSave', callback, errback)
        self.__yahoo = False

        self.__ab = ab

        self.__passport_name = passport_name # TODO : check if yahoo
        self.__contact_type = contact_type
        self.__contact_info = contact_info
        self.__invite_info = invite_info

    def __set_passport_name(self, passport_name):
        # TODO : check if eventually yahoo
        self.__passport_name = passport_name
    def __get_passport_name(self):
        return self.__passport_name
    passport_name = property(__get_passport_name, __set_passport_name,
                             doc="The passport address of the contact to " \
                                 "add. If the given address is a yahoo " \
                                 "address, this scenario will automatically " \
                                 "try to add both the MSN and Yahoo Messenger" \
                                 " accounts")

     # TODO : determine contact_type via the sharing service
    def __set_contact_type(self, contact_type):
        self.__contact_type = contact_type
    def __get_contact_type(self):
        return self.__contact_type
    contact_type = property(__get_contact_type, __set_contact_type)
    
    def __set_contact_info(self, contact_info):
        self.__contact_info = contact_info
    def __get_contact_info(self):
        return self.__contact_info
    contact_info = property(__get_contact_info, __set_contact_info,
                            doc="A dict which contains addressbook " \
                                "information about the contact")

    def __set_invite_info(self, invite_info):
        self.__invite_info = invite_info
    def __get_invite_info(self):
        return self.__invite_info
    invite_info = property(__get_invite_info, __set_invite_info,
                           doc="A dict which contains data used to " \
                               "send the invitation to the contact")

    def execute(self):
        # TODO : if self.__yahoo, always try to add as a passport address
        # then as a yahoo messenger account
        contact_info['passport_name'] = self.__passport_name
        contact_info['contact_type'] = self.__contact_type
        contact_info['is_messenger_user'] = True
        self.__ab.ContactAdd(self.__scenario, 
                             self.__contact_info,
                             self.__invite_info,
                             self.__contact_add_callback,
                             self.__contact_add_errback)
        if self.__yahoo:
            # TODO : prepare parameters and make a ContactAdd
            pass

    def __contact_add_callback(self, stuff):
        self.__callback(stuff)
        # TODO : get the cached lastchanged date to make a delta findall
        # or directly call a sync scenario
        self.__ab.FindAll(self.__scenario, True, None,
                          self.__find_all_callback, self.__find_all_errback)

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
