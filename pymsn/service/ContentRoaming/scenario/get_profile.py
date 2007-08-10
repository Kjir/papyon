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
from base import *

from pymsn.service.ContentRoaming import *

__all__ = ['GetProfileScenario']

class GetProfileScenario(BaseScenario):
    def __init__(self, storage, callback, errback, cid=''):
        """Gets the roaming profile stored on the server

            @param storage: the storage service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)            
        """
        BaseScenario.__init__(self, 'Initial', callback, errback)
        self.__storage = storage

        self.cid = cid

    def execute(self):
        self.__storage.GetProfile((self.__get_profile_callback,),
                                  (self.__get_profile_errback,),
                                  self._scenario, self.cid,
                                  True, False, False, False, True, False, 
                                  True, False, False, False, False)

    def __get_profile_callback(self, profile_rid, display_name, personal_msg):
        callback = self._callback
        callback[0](profile_rid, display_name, personal_msg, *callback[1:])

    def __get_profile_errback(self, error_code):
        errcode = ContentRoamingError.UNKNOWN
        errback = self._errback[0]
        args = self._errback[1:]
        errback(errcode, *args)
