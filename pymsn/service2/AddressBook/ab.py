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

from pymsn.service2.SOAPUtils import XMLTYPE

__all__ = ['AB']

class AB(SOAPService):
    def __init__(self, security_token, proxies=None):
        self.__security_token = security_token
        SOAPService.__init__(self, "AB", proxies)
    
    def FindAll(self, scenario, deltas_only, last_change,
            callback, errback):
        """Requests the contact list.
            @param scenario: "Initial" | ...
            @param deltas_only: True if the method should only check changes
                since last_change, otherwise False
            @param last_change: an ISO 8601 timestamp
                (previously sent by the server), or
                0001-01-01T00:00:00.0000000-08:00 to get the whole list
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        if not deltas_only: 
            last_change = self._service.ABFindAll.default_timestamp
            
        self.__call_soap_method(self._service.ABFindAll, scenario,
                (XMLTYPE.bool.encode(deltas_only), last_change),
                callback, errback)

    def ContactAdd(self, scenario, passport, is_messenger, type,
            callback, errback):
        """Adds a contact to the contact list.

            @param scenario: "ContactSave" | ...
            @param passport: the passport adress if the contact to add
            @param is_messenger: True if this is a messenger contact,
                otherwise False (only a Live mail contact)
            @param type: "Regular" | "LivePending" | "LiveAccepted" | "Messenger2"
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABContactAdd, scenario,
                (passport, XMLTYPE.bool.encode(is_messenger), type),
                callback, errback)

    def ContactDelete(self, scenario, contact_id, callback, errback):
        """Deletes a contact from the contact list.
        
            @param scenario: "Timer" | ...
            @param contact_id: the contact id (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABContactDelete, scenario,
                (contact_id), callback, errback)
        
    def ContactUpdate(self, scenario, contact_id, contact_info, 
            callback, errback):
        """Updates a contact informations.
        
            @param scenario: "ContactSave" | ...
            @param contact_id: the contact id (a GUID)
            @param contact_info: info dict
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        if 'is_messenger_user' in contact_info:
            contact_info['is_messenger_user'] = \
                    XMLTYPE.bool.encode(contact_info['is_messenger_user'])

        self.__call_soap_method(self._service.ABContactUpdate, scenario,
                                (contact_id,
                                 contact_info.get('display_name', None),
                                 contact_info.get('is_messenger_user', None),
                                 contact_info.get('first_name', None),
                                 contact_info.get('last_name', None),
                                 contact_info.get('birth_date', None),
                                 contact_info.get('email', None),
                                 contact_info.get('phone', None),
                                 contact_info.get('location', None),
                                 contact_info.get('web_site', None),
                                 contact_info.get('annotation', None),
                                 contact_info.get('comment', None),
                                 contact_info.get('anniversary', None)),
                                callback, errback)
        
    def GroupAdd(self, scenario, group_name, callback, errback):
        """Adds a group to the address book.

            @param scenario: "GroupSave" | ...
            @param group_name: the name of the group
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABGroupAdd, scenario,
                                (group_name), callback, errback)

    def GroupDelete(self, scenario, group_id, callback, errback):
        """Deletes a group from the address book.

            @param scenario: "Timer" | ...
            @param group_id: the id of the group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABGroupDelete, scenario,
                                (group_id), callback, errback)

    def GroupUpdate(self, scenario, group_id, group_name, callback, errback):
        """Updates a group name.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param group_name: the new name for the group
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABGroupUpdate, scenario,
                (group_id, group_name), callback, errback)

    def GroupContactAdd(self, scenario, group_id, contact_id, callback, errback):
        """Adds a contact to a group.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param contact_id: the id of the contact to add to the group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABGroupContactAdd, scenario,
                (group_id, contact_id), callback, errback)

    def GroupContactDelete(self, scenario, group_id, contact_id, callback, errback):
        """Deletes a contact from a group.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param contact_id: the id of the contact to delete from the group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__call_soap_method(self._service.ABGroupContactDelete, scenario,
                (group_id, contact_id), callback, errback)

    def __call_soap_method(self, method, scenario, args, callback, errback):
        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(scenario, self.__security_token)
        soap_body = method.soap_body(*args)

        self._send_request(self._service.url, soap_header, soap_body,
                soap_action, callback, errback, http_headers)
        
