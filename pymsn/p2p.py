# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
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

"""P2P
This module contains the classes needed to engage in a peer to peer transfer
with a contact."""

from event import EventsDispatcher
from msnp2p import OutgoingP2PSession, EufGuid, ApplicationID
from profile import NetworkID

import pymsn.util.ElementTree as ElementTree
import pymsn.util.StringIO as StringIO

import logging
import base64
import sha

__all__ = ['MSNObjectType', 'MSNObject', 'MSNObjectStore']

logger = logging.getLogger('p2p')


class MSNObjectType(object):
    CUSTOM_EMOTICON = 2
    DISPLAY_PICTURE = 3
    BACKGROUND_PICTURE = 5
    DYNAMIC_DISPLAY_PICTURE = 7
    WINK = 8


class MSNObject(object):
    def __init__(self, creator, size, type, location, friendly, shad=None, shac=None):
        self._creator = creator
        self._size = size
        self._type = type
        self._location = location
        self._friendly = friendly
        self._data_sha = shad
        self._checksum_sha = shac

        self.__data = None

    def __set_data(self, data):
        tmp = data.getvalue()
        data_sha = base64.b64encode(sha.new(tmp).digest())
        if self._data_sha is not None:
            if self._data_sha != data_sha:
                # TODO : error on corrupted data
                return
        else:
            self._data_sha = data_sha
        self._size = len(tmp)
        self.__data = data
        self._checksum_sha = base64.b64encode(self.__compute_checksum())
    def __get_data(self):
        return self.__data
    _data = property(__get_data, __set_data)

    @staticmethod
    def parse(client, xml_data):
        data = StringIO.StringIO(xml_data)
        element = ElementTree.parse(data).getroot().attrib
        
        creator = client.address_book.contacts.\
            search_by_account(element["Creator"]).\
            search_by_network_id(NetworkID.MSN)[0]
        size = int(element["Size"])
        type = int(element["Type"])
        location = element["Location"]
        friendly = element["Friendly"]
        shad = element.get("SHA1D", None)
        shac = element.get("SHA1C", None)

        return MSNObject(creator, size, type, location, friendly, shad, shac)

    @property
    def context(self):
        return base64.b64encode(str(self) + "\x00")

    def __compute_checksum(self):
        input = "Creator%sSize%sType%sLocation%sFriendly%sSHA1D%s" % \
            (self._creator.account, str(self._size), str(self._type),\
                 self._location, self._friendly, self._data_sha)
        return sha.new(input).digest()

    def __str__(self):
        #FIXME: we need to xml.attr_escape many of those ?
        return """<msnobj Creator="%s" Size="%s" Type="%s" Location="%s" Friendly="%s" SHA1D="%s" SHA1C="%s"/>""" % \
            (self._creator.account, str(self._size), str(self._type), \
                 self._location, self._friendly, self._data_sha, self._checksum_sha)


class MSNObjectStore(EventsDispatcher):
    def __init__(self, client):
        self._client = client
        self._outgoing_sessions = {} # session => (handle_id, callback, errback)
        self._incoming_sessions = {}
        EventsDispatcher.__init__(self)

    def request(self, msn_object, callback, errback=None):
        if msn_object._data is not None:
            callback[0](msn_object._data, *callback[1:])

        if msn_object._type == MSNObjectType.DISPLAY_PICTURE:
            application_id = ApplicationID.DISPLAY_PICTURE_TRANSFER
        else:
            raise NotImplementedError
        session = OutgoingP2PSession(self._client._p2p_session_manager, 
                                     msn_object._creator, msn_object.context, 
                                     EufGuid.MSN_OBJECT, application_id)
        handle_id = session.connect("transfer-completed",
                        self._outgoing_session_transfer_completed)
        self._outgoing_sessions[session] = (handle_id, callback, errback)

    def publish(self, msn_object, file_object):
        pass
    
    def _outgoing_session_transfer_completed(self, session, data):
        handle_id, callback, errback = self._outgoing_sessions[session]
        session.disconnect(handle_id)
        callback[0](data, *callback[1:])
        del self._outgoing_sessions[session]


