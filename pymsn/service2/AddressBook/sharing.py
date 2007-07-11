# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
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

from pymsn.service2.SOAPService import SOAPService

__all__ = ['Sharing']

class Sharing(SOAPService):
    def __init__(self, security_token, proxies=None):
        self.__security_token = security_token
        SOAPService.__init__(self, "Sharing", proxies)

    def FindMembership(self, scenario, services, deltas_only, last_change,
            callback, errback):
        """Requests the membership list.

            @param scenario: 'Initial' | ...
            @param services: a list containing the services to check in
                             ['Messenger', 'Invitation', 'SocialNetwork',
                              'Space', 'Profile' ]
            @param deltas_only: True if the method should only check changes 
                                since last_change, False else
            @param last_change: an ISO 8601 timestamp
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.FindMembership, scenario,
                (services, deltas_only, last_change),
                callback, errback)

    def AddMember(self):
        pass

    def DeleteMember(self):
        pass

    def __call_soap_method(self, method, scenario, args, callback, errback):
        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(scenario, self.__security_token)
        soap_body = method.soap_body(*args)

        self._send_request(self._service.url, soap_header, soap_body, 
                soap_action, callback, errback, http_headers)
