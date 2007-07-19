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
from pymsn.service2.SOAPUtils import XMLTYPE
from pymsn.service2.SingleSignOn import *

__all__ = ['AB']


class Group(object):
    def __init__(self, group):
        self.GroupId = self.find("./ab:groupId").text

        group_info = group.find("./ab:groupInfo")
        self.GroupType = group_info.find("./ab:groupType")
        self.Name = group_info.find("./ab:name")
        self.IsNotMobileVisible = group_info.find("./ab:IsNotMobileVisible")
        self.IsPrivate = group_info.find("./ab:IsPrivate")
        self.Annotations = annotations_to_dict(group_info.find("./ab:Annotations"))
        
        self.PropertiesChanged = [] #FIXME: implement this
        self.Deleted = XMLTYPE.bool.decode(group.find("./ab:fDeleted"))
        self.LastChanged = XMLTYPE.datetime.decode(member.find("./ab:lastChanged").text)

    def __hash__(self):
        return hash(self.GroupId)

    def __eq__(self, other):
        return self.GroupId == other.GroupId

    def __repr__(self):
        return "<Group id=%s>" % self.GroupId


class AB(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "AB", proxies)
   
    @RequireSecurityTokens(LiveService.CONTACTS)
    def FindAll(self, callback, errback, scenario,
            deltas_only, last_change=''):
        """Requests the contact list.
            @param scenario: "Initial" | "ContactSave" ...
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
            
        self.__soap_request(self._service.ABFindAll, scenario,
                (XMLTYPE.bool.encode(deltas_only), last_change),
                callback, errback)

    @RequireSecurityTokens(LiveService.CONTACTS)
    def ContactAdd(self, callback, errback, scenario,
            contact_info, invite_info):
        """Adds a contact to the contact list.

            @param scenario: "ContactSave" | ...
            @param contact_info: info dict concerning the new contact
            @param invite_info: info dict concerning the sent invite
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        is_messenger_user = contact_info.get('is_messenger_user', None)
        self.__soap_request(self._service.ContactAdd, scenario,
                (contact_info.get('passport_name', None), 
                    XMLTYPE.bool.encode(is_messenger_user),
                    contact_info.get('contact_type', None),
                    contact_info.get('first_name', None),
                    contact_info.get('last_name', None),
                    contact_info.get('birth_date', None),
                    contact_info.get('email', None),
                    contact_info.get('phone', None),
                    contact_info.get('location', None),
                    contact_info.get('web_site', None),
                    contact_info.get('annotation', None),
                    contact_info.get('comment', None),
                    contact_info.get('anniversary', None),
                    invite_info.get('display_name', None),
                    invite_info.get('invite_message', None)),
                callback, errback)

    def _HandleContactAddResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def ContactDelete(self, callback, errback, scenario,
            contact_id):
        """Deletes a contact from the contact list.
        
            @param scenario: "Timer" | ...
            @param contact_id: the contact id (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.ABContactUpdate, scenario,
                (contact_id,), callback, errback)
        
    def _HandleContactDeleteResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def ContactUpdate(self, callback, errback,
            scenario, contact_id, contact_info):
        # TODO : maybe put contact_id in contact_info
        """Updates a contact informations.
        
            @param scenario: "ContactSave" | "Timer" | ...
            @param contact_id: the contact id (a GUID)
            @param contact_info: info dict
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        if 'is_messenger_user' in contact_info:
            contact_info['is_messenger_user'] = \
                    XMLTYPE.bool.encode(contact_info['is_messenger_user'])
        
        self.__soap_request(self._service.ABContactUpdate, scenario,
                (contact_id,
                    contact_info.get('display_name', None),
                    contact_info.get('is_messenger_user', None),
                    contact_info.get('contact_type', None),
                    contact_info.get('first_name', None),
                    contact_info.get('last_name', None),
                    contact_info.get('birth_date', None),
                    contact_info.get('email', None),
                    contact_info.get('phone', None),
                    contact_info.get('location', None),
                    contact_info.get('web_site', None),
                    contact_info.get('annotation', None),
                    contact_info.get('comment', None),
                    contact_info.get('anniversary', None),
                    contact_info.get('has_space', None)),
                callback, errback)

    def _HandleContactUpdateResponse(self, request_id, callback, errback, response):
        pass
        
    @RequireSecurityTokens(LiveService.CONTACTS)
    def GroupAdd(self, callback, errback, scenario,
            group_name):
        """Adds a group to the address book.

            @param scenario: "GroupSave" | ...
            @param group_name: the name of the group
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.ABGroupAdd, scenario,
                (group_name,),
                callback, errback)

    def _HandleGroupAddResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def GroupDelete(self, callback, errback, scenario,
            group_id):
        """Deletes a group from the address book.

            @param scenario: "Timer" | ...
            @param group_id: the id of the group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.ABGroupDelete, scenario,
                (group_id,), callback, errback)

    def _HandleGroupDeleteResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def GroupUpdate(self, callback, errback, scenario,
            group_id, group_name):
        """Updates a group name.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param group_name: the new name for the group
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.ABGroupUpdate, scenario,
                (group_id, group_name), callback, errback)

    def _HandleGroupUpdateResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def GroupContactAdd(self, callback, errback, scenario,
            group_id, contact_id):
        """Adds a contact to a group.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param contact_id: the id of the contact to add to the
                               group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.ABGroupContactAdd, scenario,
                (group_id, contact_id), callback, errback)

    def _HandleContactAddResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def GroupContactDelete(self, callback, errback, scenario,
            group_id, contact_id):
        """Deletes a contact from a group.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param contact_id: the id of the contact to delete from the 
                               group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.ABGroupContactDelete, scenario,
                (group_id, contact_id), callback, errback)

    def _HandleContactDeleteResponse(self, request_id, callback, errback, response):
        pass

    def __soap_request(self, method, scenario, args, callback, errback):
        token = str(self._tokens[LiveService.CONTACTS])

        http_headers = method.transport_headers()
        soap_action = method.soap_action()

        soap_header = method.soap_header(scenario, token)
        soap_body = method.soap_body(*args)
        
        method_name = method.__name__.rsplit(".", 1)[1]
        self._send_request(method_name,
                self._service.url, 
                soap_header, soap_body, soap_action, 
                callback, errback,
                http_headers)


if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging
    from pymsn.service2.SingleSignOn import *

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

    sso = SingleSignOn(account, password)
    ab = AB(sso)
    ab.FindAll(None, None, 'Initial', False)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
