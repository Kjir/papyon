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

import contactcardservice
import scenario

from pymsn.service.SOAPUtils import *

import pymsn.util.ElementTree as ElementTree
import pymsn.util.StringIO as StringIO
import gobject

import logging

__all__ = ['Spaces']

class Spaces(gobject.GObject):

    __gsignals__ = {
            "contact-card-retreived" : (gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (object, object))
            }

    __gproperties__ = {}
    def __init__(self, sso, proxies=None):
        gobject.GObject.__init__(self)

        self._ccard = contactcardservice.ContactCardService(sso, proxies)

    # Public API
    def get_contact_card(self, contact):
        ccs = scenario.GetContactCardScenario(self._ccard,
                                              contact,
                                              (self.__get_contact_card_cb, contact),
                                              (self.__get_contact_card_errback,))
        ccs()

    def __get_contact_card_cb(self, ccard, contact):
        print "Contact card retreived : \n%s\n"  % str(ccard)
        self.emit('contact-card-retreived', contact, ccard)

    def __get_contact_card_errback(self, error_code, *args):
        print "The fetching of the contact card returned an error (%s)" % error_code
