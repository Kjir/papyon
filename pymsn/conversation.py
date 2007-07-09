# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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

"""Conversation
This module contains the class needed to have a conversation with a
contact."""

from transport import *
from event import ClientState, ClientErrorType

import msnp
from switchboard_manager import SwitchboardClient

import logging
import gobject
from urllib import quote, unquote

__all__ = ['Conversation','TextFormat']

logger = logging.getLogger('conversation')

class Conversation(SwitchboardClient):
    def __init__(self, client, contacts):
        SwitchboardClient.__init__(self, client, contacts)
        self._events_handlers = set()
    
    @staticmethod
    def can_handle_message(message, switchboard_client=None):
        content_type = message.content_type[0]
        if switchboard_client is None:
            return content_type in ('text/plain', 'text/x-msnmsgr-datacast')
        return content_type in ('text/plain', 'text/x-msmsgscontrol',
                'text/x-msnmsgr-datacast')

    def send_text_message(self, text, formatting=None):
        """Build and send a text message to all persons in this
        switchboard.
        
            @param text: the text message to send.
            @type text: string"""
        content_type = ("text/plain","utf-8")
        body = text.encode("utf-8")
        ack = msnp.MessageAcknowledgement.HALF
        headers = {}
        if formatting is not None: 
            headers["X-MMS-IM-Format"] = str(formatting)
        self._send_message(content_type, body, headers, ack)

    def send_nudge(self):
        """Sends a nudge to the contacts on this switchboard."""
        content_type = "text/x-msnmsgr-datacast"
        body = "ID: 1\r\n\r\n".encode('UTF-8') #FIXME: we need to figure out the datacast objects :D
        ack = msnp.MessageAcknowledgement.NONE
        self._send_message(content_type, body, ack=ack)

    def send_typing_notification(self):
        """Sends an user typing notification to the contacts on this switchboard"""
        content_type = "text/x-msmsgscontrol"
        body = "\r\n\r\n".encode('UTF-8')
        headers = { "TypingUser" : self._client.profile.account.encode('UTF_8') }
        ack = msnp.MessageAcknowledgement.NONE
        self._send_message(content_type, body, headers, ack)
    
    def invite_user(self, contact):
        """Request a contact to join in the conversation.
            
            @param contact: the contact to invite.
            @type contact: L{profile.Contact}"""
        self._invite_user(contact)

    def leave(self):
        """Leave the conversation."""
        self._leave()

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
    
    def _on_message_received(self, message):
        message_type = message.content_type[0]
        sender_account = message.account
        sender_friendly_name = message.friendly_name
        
        senders = self._client.address_book.contacts.\
                search_by_account(sender_account)
        if len(senders) == 0:
            sender = pymsn.profile.Contact(id=0,
                    network_id=pymsn.profile.NetworkID.MSN,
                    account=account,
                    display_name=display_name)
        else:
            sender = senders.get_first()

        if message_type == 'text/plain':
            self._dispatch("on_conversation_message_received",
                           sender, unicode(message.body, message.content_type[1]),
                           TextFormat.parse(message.headers["X-MMS-IM-Format"]))
        if message_type == 'text/x-msmsgscontrol':
            self._dispatch("on_conversation_user_typing", sender)
        if message_type == 'text/x-msnmsgr-datacast' and \
                message.body.strip() == "ID: 1":
            self._dispatch("on_conversation_nudge_received",
                    sender)

    def _on_message_sent(self, message):
        pass


class TextFormat(object):
    
    DEFAULT_FONT = 'MS Sans Serif'
    
    BOLD = 1
    ITALIC = 2
    UNDERLINE = 4
    STRIKETHROUGH = 8

    @staticmethod
    def parse(format):
        text_format = TextFormat()
        text_format.__parse(format)
        return text_format

    @property
    def font(self):
        return self._font
    
    @property
    def style(self):
        return self._style

    @property
    def color(self):
        return self._color

    @property
    def right_alignment(self):
        return self._right_alignment

    @property
    def family(self):
        return self._family

    def __init__(self, font=quote(DEFAULT_FONT), style=0, color='0', 
                 right_alignment=False, family=None):
        self._font = font
        self._style = style
        self._color = color
        self._right_alignment = right_alignment
        self._family = family
    
    def __parse(self, format):
        for property in format.split(';'):
            key, value =  [str.upper(p.strip()) for p in property.split('=', 1)]
            if key == 'FN':
                # Font
                self._font = unquote(value)
            elif key == 'EF':
                # Effects
                if 'B' in value: self._style |= TextFormat.BOLD
                if 'I' in value: self._style |= TextFormat.ITALIC
                if 'U' in value: self._style |= TextFormat.UNDERLINE
                if 'S' in value: self._style |= TextFormat.STRIKETHROUGH
            elif key == 'CO':
                # Color
                value = str.zfill(value, 6)
                self._color = ''.join((value[4:6], value[2:4], value[0:2]))
            elif key == 'CS':
                # Charset
                pass
            elif key == 'PF':
                # Pitch and family
                self._family = value
            elif key == 'RL':
                # Right alignment
                if value == '1': self._right_alignement = True

    def __str__(self):
        style = ''
        if self._style & TextFormat.BOLD == TextFormat.BOLD: 
            style += 'B'
        if self._style & TextFormat.ITALIC == TextFormat.ITALIC: 
            style += 'I'
        if self._style & TextFormat.UNDERLINE == TextFormat.UNDERLINE: 
            style += 'U'
        if self._style & TextFormat.STRIKETHROUGH == TextFormat.STRIKETHROUGH: 
            style += 'S'
        
        color = '%s%s%s' % (self._color[4:6], self._color[2:4], self._color[0:2])

        format = 'FN=%s; EF=%s; CO=%s'  % (quote(self._font), style, color)

        if self._family is not None: format += '; PF=%s' % self._family
        if self._right_alignment: format += '; RL=1'
        
        return format

    def __repr__(self):
        return __str__(self)
        
