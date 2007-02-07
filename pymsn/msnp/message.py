# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

"""MSN protocol special command : MSG

G{classtree Message, IncomingMessage, OutgoingMessage}"""

from pymsn.gnet.message.HTTP import HTTPMessage

from urllib import quote, unquote

__all__ = ['MessageAcknowledgement', 'Message', 'IncomingMessage', 'OutgoingMessage']

class MessageAcknowledgement(object):
    """Message Acknowledgement"""
    FULL = 'A'
    """Acknowledgement required for both delivery success and failure"""
    MSNC = 'D'
    """Direct connection, no acknowledgment required from the server"""
    HALF = 'N'
    """Acknowledgment on delivery failures"""
    NONE = 'U'
    """No Acknowledgment"""

class Message(HTTPMessage):
    """Base Messages class.
    
        @ivar passport: sender passport
        @type passport: string
        
        @ivar friendly_name: sender friendly name
        @type friendly_name: string
        
        @ivar body: message body
        @type body: string
        
        @ivar headers: message headers
        @type headers: {header_name: string => header_value:string}
        
        @ivar content_type: the message content type
        @type content_type: tuple(mime_type, encoding)"""

    def __init__(self, body=""):
        """Initializer
            
            @param body: The body of the message, it is put after the headers
            @type body: string"""
        HTTPMessage.__init__(self)
        self.passport = 'Hotmail'
        self.friendly_name = 'Hotmail'
        self.body = body
        self.headers = {'MIME-Version' : '1.0', 'Content-Type' : 'text/plain'}


    def __repr__(self):
        """Represents the payload of the message"""
        message = ''
        if 'Content-Type' in self.headers:
            message += '\tContent-Type: ' + self.headers['Content-Type']
        else:
            message += '\tContent-Type: text/plain'
        message += '\r\n' + '\tHeaders-count: ' + str(len(self.headers))
        message += '\r\n' + '\t[message body]'
        return message

    def __get_content_type(self):
        if 'Content-Type' in self.headers:
            content_type = self.headers['Content-Type'].split(';', 1)
            if len(content_type) == 1:
                return (content_type[0].strip(), 'UTF-8')
            mime_type = content_type[0].strip()
            encoding = content_type[1].split('=', 1)[1].strip()
            return (mime_type, encoding)
        return ('text/plain', 'UTF-8')
    
    def __set_content_type(self, content_type):
        if len(content_type) == 1:
            content_type = (content_type, 'UTF-8')
        content_type = '; charset='.join(content_type)
        self.headers['Content-Type'] = content_type

    content_type = property(__get_content_type, __set_content_type,
            doc="a tuple specifying the content type")


class IncomingMessage(Message):
    """Incoming Message abstraction"""

    def __init__(self, command):
        """Initializer
        
            @param command: the MSG command received from the server
            @type command: L{command.Command}"""
        Message.__init__(self)
        self.passport = command.arguments[0]
        self.friendly_name = unquote(command.arguments[1])
        self.parse(command.payload)

    def __str__(self):
        """Represents the message
        
        the representation looks like this ::
            MSG sender-passport sender-friendly-name payload-size\\r\\n
            header1: header-content\\r\\n
            ...\\r\\n
            \\r\\n
            body
            
        @rtype: string"""
        message = Message.__str__(self)
        command = 'MSG %s %s %u\r\n' % (   self.passport,
                                            quote(self.friendly_name),
                                            len(message))
        return command + message
    
    def __repr__(self):
        """Represents the message"""
        message = Message.__repr__(self)
        length = len(Message.__str__(self))
        command = 'MSG %s %s %u\r\n' % (   self.passport,
                                            quote(self.friendly_name),
                                            length)
        return command + message


class OutgoingMessage(Message):
    """Build MSG commands destined to be sent."""

    def __init__(self, transaction_id, ack):
        """Initializer
        
            @param transaction_id: the transaction ID
            @type transaction_id: integer
            
            @param ack: Acknowledgment type
            @type ack: L{message.MessageAcknowledgement}"""
        Message.__init__(self)
        self.transaction_id = transaction_id
        self.ack = ack
        self.passport = ''
        self.friendly_name = ''

    def __str__(self):
        """Represents the message
        
        the representation looks like this ::
            MSG transaction-id ack payload-size\\r\\n
            header1: header-content\\r\\n
            ...\\r\\n
            \\r\\n
            body
            
        @rtype: string"""
        message = Message.__str__(self)
        command = 'MSG %u %s %u\r\n' % \
                (self.transaction_id, self.ack, len(message) )
        return command + message

    def __repr__(self):
        """Represents the message"""
        message = Message.__repr__(self)
        length = len(Message.__str__(self))
        command = 'MSG %u %s %u\r\n' % \
                (self.transaction_id, self.ack, length )
        return command + message
