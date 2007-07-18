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

__all__ = ['Sharing']

class Member(object):
    def __init__(self, role, member):
        self.Role = role
        self.MembershipId = XMLTYPE.int.decode(member.find("./ab:MembershipId").text)
        self.Type = member.find("./ab:Type").text
        try:
            self.DisplayName = member.find("./ab:DisplayName").text
        except AttributeError:
            self.DisplayName = ""
        self.State = member.find("./ab:State").text

        self.Deleted = XMLTYPE.bool.decode(member.find("./ab:Deleted").text)
        self.LastChanged = XMLTYPE.datetime.decode(memeber.find("./ab:LastChanged").text)
        self.Changes = [] # FIXME: extract the changes

    @staticmethod
    def new(role, member):
        type = member.find("./ab:Type").text
        if type == "Passport":
            return PassportMember(role, member)
        elif type == "Email":
            return EmailMember(role, member)
        else:
            raise NotImplementedError("Member type not implemented : " + type)

class PassportMember(Member):
    def __init__(self, role, member):
        Member.__init__(self, role, member)
        self.PassportId = XMLTYPE.int.decode(member.find("./ab:PassportId").text)
        self.PassportName = member.find("./ab:PassportName").text
        self.IsPassportNameHidden = XMLTYPE.bool.decode(member.find("./ab:find").text)
        self.CID = XMLTYPE.int.decode(member.find("./ab:CID").text)
        self.PassportChanges = [] # FIXME: extract the changes

def EmailMember(MemberA):
    def __init__(self, role, member):
        Member.__init__(self, role, member)
        self.Email = member.find("./ab:Email")


class Sharing(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "Sharing", proxies)

    @RequireSecurityTokens(LiveService.CONTACTS)
    def FindMembership(self, callback, errback, scenario,
            services, deltas_only, last_change=''):
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
        self.__soap_request(self._service.FindMembership, scenario,
                (services, deltas_only, last_change), callback, errback)
        
    def _HandleFindMembershipResponse(self, request_id, callback, errback, response):
        memberships = []
        for role, members in response.iteritems():
            for member in members:
                memberships.append(Member.new(role, member))
        callback[0](memberships, *callback[1:])

    @RequireSecurityTokens(LiveService.CONTACTS)
    def AddMember(self, callback, errback, scenario,
            member_role, passport_member):
        """Adds a member to a membership list.

            @param scenario: 'Timer' | 'BlockUnblock' | ...
            @param member_role: 'Allow' | ...
            @param passport_member: tuple(type, state, passport) with
                                    type in ['Passport', ...] and 
                                    state in ['Accepted', ...]
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        type, state, passport = passport_member
        self.__soap_request(self._service.AddMember, scenario,
                (member_role, type, state, passport), callback, errback)

    def _HandleAddMemberResponse(self, request_id, callback, errback, response):
        pass

    @RequireSecurityTokens(LiveService.CONTACTS)
    def DeleteMember(self, callback, errback, scenario,
            member_role, passport_member):
        """Deletes a member from a membership list.

            @param scenario: 'Timer' | 'BlockUnblock' | ...
            @param member_role: 'Block' | ...
            @param passport_member: tuple(type, state, membership_id)
                                    type in ['Passport', ...] and 
                                    state in ['Accepted', ...]
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        type, state, membership = passport_member
        self.__soap_request(self._service.DeleteMember, scenario,
                (member_role, type, state, membership), callback, errback)

    def _HandleDeleteMemberResponse(self, request_id, callback, errback, response):
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
    sharing = Sharing(sso)
    sharing.FindMembership(None, None, 'Initial',
            ['Messenger', 'Invitation'], False)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
