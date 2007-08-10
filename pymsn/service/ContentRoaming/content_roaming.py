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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# import pymsn.service.ContentRoaming.storage as storage
# import pymsn.service.ContentRoaming.scenario as scenario

import storage
from pymsn.service.ContentRoaming.scenario import *

import gobject

__all__ = ['ContentRoaming', 'ContentRoamingState', 'ContentRoamingError']

class ContentRoamingError(object):
    UNKNOWN = 0

class ContentRoamingState(object):
    """Content roaming service synchronization state.

    The service is said to be synchronized when it
    matches the stuff stored on the server."""

    NOT_SYNCHRONIZED = 0
    """The service is not synchronized yet"""
    SYNCHRONIZING = 1
    """The service is being synchronized"""
    SYNCHRONIZED = 2
    """The service is already synchronized"""

class ContentRoaming(gobject.GObject):

    __gproperties__ = {
        "state"            :  (gobject.TYPE_INT,
                               "State",
                               "The state of the addressbook.",
                               0, 2, ContentRoamingState.NOT_SYNCHRONIZED,
                               gobject.PARAM_READABLE),

        "display-name"     : (gobject.TYPE_STRING,
                              "Display name",
                              "The user's display name",
                              "",
                              gobject.PARAM_READABLE),
        
        "personal-message" : (gobject.TYPE_STRING,
                              "Personal message",
                              "The user's personal message",
                              "",
                              gobject.PARAM_READABLE)
        }

    def __init__(self, sso, ab, proxies=None):
        """The content roaming object"""
        gobject.GObject.__init__(self)

        self._storage = storage.Storage(sso, proxies)
        self._ab = ab

        self._profile_id = None

        self.__state = ContentRoamingState.NOT_SYNCHRONIZED
        self.__display_name = ''
        self.__personal_message = ''

    # Properties
    def __get_state(self):
        return self.__state
    def __set_state(self, state):
        self.__state = state
        self.notify("state")
    state = property(__get_state)
    _state = property(__get_state, __set_state)
        
    @property
    def display_name(self):
        return self.__display_name

    @property
    def personal_message(self):
        return self.__personal_message

    def sync(self):
        if self._state != ContentRoamingState.NOT_SYNCHRONIZED:
            return
        self._state = ContentRoamingState.SYNCHRONIZING

        gp = GetProfileScenario(self._storage,
                                (self.__get_profile_cb,),
                                (self.__common_errback,))
        gp.cid = self._ab.profile.cid
        gp()

    # Public API
    def store(self, display_name=None, personal_message=None):
        if display_name is None:
            display_name = self.__display_name
        if personal_message is None:
            personal_message = self.__personal_message

        up = UpdateProfileScenario(self._storage,
                                   (self.__update_profile_cb,),
                                   (self.__common_errback,))
        up.profile_id = self._profile_id
        up.display_name = display_name
        up.personal_message = personal_message
        up()
    # End of public API

    def __get_profile_cb(self, profile_rid, display_name, personal_message):
        self._profile_id = profile_rid

        self.__display_name = display_name
        self.__personal_message = personal_message

        self._state = ContentRoamingState.SYNCHRONIZED

    def __update_profile_cb(self):
        pass

    # Callbacks
    def __common_errback(self, error_code, *args):
        print "The content roaming service got the error (%s)" % error_code

gobject.type_register(ContentRoaming)

if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging
    from pymsn.service.SingleSignOn import *
    from pymsn.service.AddressBook import *

    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)
    
    signal.signal(signal.SIGTERM,
            lambda *args: gobject.idle_add(mainloop.quit()))

    def address_book_state_changed(address_book, pspec, sso):
        if address_book.state == AddressBookState.SYNCHRONIZED:

            def content_roaming_state_changed(cr, pspec):
                if cr.state == ContentRoamingState.SYNCHRONIZED:
                    cr.store("Huhihuha", "This is my P-M-S-G dude.")

            cr = ContentRoaming(sso, address_book)
            cr.connect("notify::state", content_roaming_state_changed)
            cr.sync()

    sso = SingleSignOn(account, password)

    address_book = AddressBook(sso)
    address_book.connect("notify::state", address_book_state_changed, sso)
    address_book.sync()

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
