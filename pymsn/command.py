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

"""A set of classes abstracting the MSN protocol commands, basically all MSN
core protocol commands look almost the same."""

from gnet.message.HTTP import HTTPMessage

from urllib import quote, unquote

__all__ = ['Command', 'Message', 'IncomingMessage', 'OutgoingMessage']

class Command(object):
    """Abstraction of MSN commands, this class enables parsing and construction
    of commands.
    
        @ivar name: the 3 uppercase letters name of the command
        @type name: string
        
        @ivar transaction_id: the transaction id of the command or None
        @type transaction_id: integer
        
        @ivar arguments: the arguments of the command
        @type arguments: tuple()
        
        @ivar payload: the payload of the command
        @type payload: string or None"""

    OUTGOING_NO_TRID = ('OUT', 'PNG')
    INCOMING_NO_TRID = (
            # NS commands
            'QNG', 'IPG', 'NOT', 'NLN', 'FLN', 'GCF',
            'QRY', 'SBS', 'UBN', 'UBM', 'UBX', 
            # SW commands
            'RNG', 'JOI', 'BYE', 'MSG')

    OUTGOING_PAYLOAD = (
            'QRY', 'SDC', 'PGD', 'ADL', 'RML', 'UUN',
            'UUM', 'UUX', 'MSG')

    INCOMING_PAYLOAD = (
            'GCF', 'MSG', 'UBN', 'UBM', 'UBX', 'IPG',
            'NOT')

    def __init__(self):
        self._reset()

    def _reset(self):
        """Resets the object values"""
        self.name = ''
        self.transaction_id = None
        self.arguments = None
        self.payload = None

    ### public methods
    def build(self, name, transaction_id, payload=None, *arguments):
        """Updates the command with the given parameters

            @param name: the command name (3 letters) (e.g. MSG NLN ...)
            @type name: string
            
            @param transaction_id: the transaction ID
            @type transaction_id: integer
            
            @param *arguments: the command arguments
            @type *arguments: string, ... 
            
            @param payload: is the data to send with the command
            @type payload: string
        """
        self.name = name
        self.transaction_id = transaction_id
        self.arguments = arguments
        self.payload = payload

    def parse(self, buf):
        """Fills the Command object according parsing a string.
            
            @param buf: the data to parse
            @type buf: string"""
        self.__init_state()
        lines = buf.split('\r\n', 1)
        self.__parse_command(lines[0])
        if len(lines) > 1: # payload
            self.payload = lines[1]
            # remove the last argument as it is the data length
            self.arguments = self.arguments[:-1]

    def is_error(self):
        """Tells if the current command is an error code
            
            @rtype: bool"""
        try:
            int(self.name)
        except ValueError:
            return False
        else:
            return True

    def is_payload(self):
        """Tells if the current comment is a payload command
        
            @rtype: bool"""
        return self.payload is not None

    ### private and special methods
    def __str__(self):
        result = self.name[:]
        if self.transaction_id is not None:
            result += ' ' + str(self.transaction_id)

        if self.arguments is not None and len(self.arguments) > 0:
            result += ' ' + ' '.join(self.arguments)

        if self.payload is not None:
            length = len(self.payload)
            if length > 0:
                result += ' ' + str(length) + '\r\n' + self.payload
                return result

        return result + '\r\n'

    def __repr__(self):
        result = self.name[:]
        if self.transaction_id is not None:
            result += ' ' + str(self.transaction_id)

        if self.arguments is not None and len(self.arguments) > 0:
            result += ' ' + ' '.join(self.arguments)

        if self.payload is not None:
            length = len(self.payload)
            if length > 0:
                result += ' ' + str(length) + '\r\n' + '\t[payload]'
                return result
        return result

    def __parse_command(self, buf):
        words = buf.split()
        self.name, pos = words[0], 1
        if (words[0] not in self.INCOMING_NO_TRID) and\
                (words[0] not in self.OUTGOING_NO_TRID) and\
                len(words) > pos:
            self.transaction_id = int(words[pos])
            pos += 1
        if len(words) > pos:
            self.arguments = words[pos:]

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
            @type command: L{structure.Command}"""
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
            @type ack: L{consts.MessageAcknowledgement}"""
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
