# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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

"""pymsn event interfaces.

Defines the interfaces that the client can implement to benefit from the
client event notifications."""

class EventsDispatcher(object):

    def __init__(self):
        self._events_handlers = set()

    ### Callbacks
    def register_events_handler(self, events_handler):
        """
        events_handler:
            an instance with methods as code of callbacks.
        """
        self._events_handlers.add(events_handler)

    def _dispatch(self, name, *args):
        count = 0
        for event_handler in list(self._events_handlers):
            if event_handler._dispatch_event(name, *args):
                count += 1
        return count

from client import *
from conversation import *
from contact import *
from address_book import *
from offline_messages import *
from invite import *
