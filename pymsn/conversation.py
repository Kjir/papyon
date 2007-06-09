# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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

"""Conversation
This module contains the class needed to have a conversation with a
contact."""

from transport import *
from event import ClientState, ClientErrorType

import msnp
from switchboard_manager import SwitchboardClient

import logging
import gobject

__all__ = ['Conversation']

logger = logging.getLogger('conversation')


class Conversation(SwitchboardClient):
    def __init__(self, client, contacts):
        SwitchboardClient.__init__(self, client, contacts)
        self._events_handlers = set()
    
    def send_text_message(self, text):
        """Build and send a text message to all persons in this
        switchboard.
        
            @param text: the text message to send.
            @type text: string"""
        content_type = ("text/plain","UTF-8")
        body = text.encode('UTF-8')
        ack = msnp.MessageAcknowledgement.HALF
        self._send_message(content_type, body, ack)

    def send_nudge(self):
        """Sends a nudge to the contacts on this switchboard."""
        content_type = "text/x-msnmsgr-datacast"
        body = "ID: 1\r\n\r\n".encode('UTF-8') #FIXME: we need to figure out the datacast objects :D
        ack = msnp.MessageAcknowledgement.NONE
        self._send_message(content_type, body, ack)
    
    def invite_user(self, contact):
        """Request a contact to join in the conversation.
            
            @param contact: the contact to invite.
            @type contact: L{profile.Contact}"""
        self._invite_user(contact)

    def leave_conversation(self):
        """Leave the conversation."""
        pass

    ### Callbacks
    def register_events_handler(self, events_handler):
        """
        events_handler:
            an instance with methods as code of callbacks.
        """
        self._events_handlers.add(events_handler)

    def _dispatch(self, name, *args):
        for event_handler in self._events_handlers:
            event_handler._dispatch_event(name, *args)

    def _on_contact_joined(self, contact):
        self._dispatch("on_conversation_user_joined", contact)

    def _on_contact_left(self, contact):
        self._dispatch("on_conversation_user_left", contact)

