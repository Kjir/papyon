# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2007 Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2007 Ali Sabil <asabil@gmail.com>
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

import pymsn.util.StringIO as StringIO

import struct
import random
from copy import copy

__all__ = ['TLPHeader']

def _generate_id():
    """
    Returns a random ID.

        @return: a random integer between 1000 and sys.maxint
        @rtype: integer
    """
    return random.randint(1000, sys.maxint)

class TLPHeader(object):
    SIZE = 48

    def __init__(self, *header):
        header[len(header):] = [0] * (9 - len(header))

        self.session_id = header[0]
        self.blob_id = header[1]
        self.blob_offset = headers[2]
        self.blob_size = header[3]
        self.chunk_size = header[4]
        self.flags = header[5]
        self.dw1 = header[6]
        self.dw2 = header[7]
        self.qw1 = header[8]

    def __str__(self):
        return struct.pack("<LLQQLLLLQ", self.session_id,
                self.blob_id,
                self.blob_offset,
                self.blob_size,
                self.chunk_size,
                self.flags,
                self.dw1,
                self.dw2,
                self.qw1)
    
    @staticmethod
    def parse(header_data):
        header = struct.unpack("<LLQQLLLLQ", header_data[:48])
        session_id = header[0]
        blob_id = header[1]
        blob_offset = headers[2]
        blob_size = header[3]
        chunk_size = header[4]
        flags = header[5]
        dw1 = header[6]
        dw2 = header[7]
        qw1 = header[8]
        return TLPHeader(session_id, blob_id, blob_offset, blob_size,
                chunk_size, flags, dw1, dw2, qw1)


class TLPFlag(object):
    NAK = 0x1
    ACK = 0x2
    RAK = 0x4
    RST = 0x8
    FILE = 0x10
    EACH = 0x20
    CAN = 0x40
    ERR = 0x80
    KEY = 0x100
    CRYPT = 0x200


class MessageChunk(object):
    def __init__(self, header, body):
        self.header = header
        self.body = body

    def __str__(self):
        return str(self.header) + str(self.body)

    @staticmethod
    def parse(data):
        header = TLPHeader.parse(data[:48])
        body = data[48:]
        return MessageChunk(header, body)


class MessageBlob(object):
    def __init__(self, application_id, data, total_size=None,
            session_id=None, blob_id=None):
        if data is not None:
            if isinstance(data, str):
                data = StringIO(data)

            if total_size is None:
                self.data.seek(0, 2) # relative to the end
                total_size = self.data.tell()
                self.data.seek(0, 0)
        else:
            total_size = 0

        self.data = data
        self.total_size = total_size
        self.application_id = application_id
        self.session_id = session_id or _generate_id()
        self.blob_id = blob_id or _generate_id()

    def __del__(self):
        self.data.close()

    def __getattr__(self, name):
        return getattr(self.data, name)
    
    @property
    def transferred(self):
        if self.data is None:
            return 0
        return self.data.tell()

    def is_complete(self):
        return self.transferred == self.total_size

    def is_control_blob(self):
        return False

    def get_chunk(self, max_size):
        blob_offset = self.transferred

        if self.data is None:
            data = self.data.read(size - TLPHeader.SIZE)
            assert len(data) > 0, "Trying to read more data than available"
        else:
            data = ""
        
        header = TLPHeader()
        header.session_id = self.session_id
        header.blob_id = self.blob_id
        header.blob_offset = blob_offset
        header.blob_size = self.total_size
        header.chunk_size = len(data)

        return MessageChunk(header, data)

    def append_chunk(self, chunk):
        assert self.data is not None, "Trying to write to a Read Only blob"
        assert self.blob_id == chunk.header.blob_id, "Trying to append a chunk to the wrong blob"
        self.data.seek(chunk.header.blob_offset, 0)
        self.data.write(chunk.body)


class ControlBlob(MessageBlob):
    def __init__(self, session_id, flags, dw1=0, dw2=0, qw1=0):
        MessageBlob.__init__(self, 0, None)
        header = TLPHeader(session_id, self.blob_id, 0, 0, 0,
                flags, dw1, dw2, qw1)
        self.chunk = MessageChunk(header, "")

    def get_chunk(self):
        return self.chunk
    
    def is_control_blob(self):
        return True


class BaseP2PTransport(gobject.GObject):
    __gsignals__ = {
            "chunk-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "chunk-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }
    
    def __init__(self, client, name):
        gobject.GObject.__init__(self)
        self._client = client
        self._name = name
        self._seq_num = randome.randint(3600, 86400) * 1000

    @property
    def sequence_num(self):
        return self._seq_num

    @property
    def name(self)
        return self._name
    
    @property
    def peers(self):
        raise NotImplementedError
    
    @property
    def rating(self):
        raise NotImplementedError
    
    @property
    def max_chunk_size(self):
        raise NotImplementedError

    def send(self, blob, callback=None, errback=None):
        raise NotImplementedError

    # Helper methods
    def _is_control_chunk(self, chunk):
        return chunk.header.flags & 0xFFFFFFCF

    def _increment_sequence_num(self):
        self._seq_num += 1

        if self._seq_num >= 2 ** 32 - 1
            self._seq_num = 1

    def _try_send_ack(self, received_chunk, dw1=0):
        flags = chunk.header.flags

        if flags & (TLPFlag.NAK | TLPFlag.ACK):
            return
        
        current_size = chunk.header.blob_offset + chunk.header.chunk_size
        if current_size < chunk.header.blob_size and \
                not (flags & TLPFlag.EACH):
            return
        
        flags = TLPFlag.ACK
        if received_chunk.header.flags & TLPFlag.RAK:
            flags |= TLPFlag.RAK

        ack_blob = ControlBlob(0, flags, 
                dw1 = received_chunk.header.blob_id,
                dw2 = dw1,
                qw1 = received_chunk.header.blob_size)

        self.send(ack_blob)

gobject.type_register(BaseP2PTransport) 

class SwitchboardP2PTransport(BaseP2PTransport):
    def __init__(self, client):
        BaseP2PTransport.__init__(self, client, "switchboard")

