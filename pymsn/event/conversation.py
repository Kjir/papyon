# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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

"""Conversation event interfaces

The interfaces defined in this module allow receiving notification events
from a L{Conversation<pymsn.conversation.ConversationInterface>} object."""

from pymsn.event import BaseEventInterface

__all__ = ["ConversationEventInterface"]

class ConversationEventInterface(BaseEventInterface):
    """interfaces allowing the user to get notified about events
    from a L{Conversation<pymsn.conversation.ConversationInterface>} object."""

    def __init__(self, conversation):
        """Initializer
            @param conversation: the conversation we want to be notified for its events
            @type conversation: L{Conversation<pymsn.conversation.ConversationInterface>}"""
        BaseEventInterface.__init__(self, conversation)

    def on_conversation_state_changed(self, state):
        """@attention: not implemented"""
        pass

    def on_conversation_error(self, type, error):
        """@attention: not implemented"""
        pass

    def on_conversation_user_joined(self, contact):
        """Called when a user joins the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<pymsn.profile.Contact>}"""
        pass

    def on_conversation_user_left(self, contact):
        """Called when a user leaved the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<pymsn.profile.Contact>}"""
        pass

    def on_conversation_user_typing(self, contact):
        """Called when a user is typing.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<pymsn.profile.Contact>}"""
        pass

    def on_conversation_message_received(self, sender, message):
        """Called when a user sends a message.
            @param sender: the contact who sent the message
            @type sender: L{Contact<pymsn.profile.Contact>}

            @param message: the message
            @type message: L{ConversationMessage<pymsn.conversation.ConversationMessage>}"""
        pass
    
    def on_conversation_nudge_received(self, sender):
        """Called when a user sends a nudge.
            @param sender: the contact who sent the nudge
            @type sender: L{Contact<pymsn.profile.Contact>}"""
        pass

