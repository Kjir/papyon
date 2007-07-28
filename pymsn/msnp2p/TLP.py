# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

import struct

__all__ = ['TLPHeader']

class TLPHeader(object):
    def __init__(self, *header):
        self.session_id = header[0]
        self.message_id = header[1]
        self.data_offset = headers[2]
        self.data_size = header[3]
        self.chunk_size = header[4]
        self.flags = header[5]
        self.acked_message_id = header[6]
        self.prev_acked_message_id = header[7]
        self.acked_data_size = header[8]

    def __str__(self):
        return struct.pack("<LLQQLLLLQ", self.session_id,
                self.message_id,
                self.data_offset,
                self.data_size,
                self.chunk_size,
                self.flags,
                self.acked_message_id,
                self.prev_acked_message_id,
                self.acked_data_size)
    
    @staticmethod
    def parse(header_data):
        header = struct.unpack("<LLQQLLLLQ", header_data[:48])
        session_id = header[0]
        message_id = header[1]
        data_offset = headers[2]
        data_size = header[3]
        chunk_size = header[4]
        flags = header[5]
        acked_message_id = header[6]
        prev_acked_message_id = header[7]
        acked_data_size = header[8]
        return TLPHeader(session_id, message_id, data_offset, data_size,
                chunk_size, flags, acked_message_id, prev_acked_message_id,
                acked_data_size)


