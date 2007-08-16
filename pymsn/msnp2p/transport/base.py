# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
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

from pymsn.msnp2p.transport.TLP import TLPFlag, MessageChunk, ControlBlob

import gobject
import logging

__all__ = ['BaseP2PTransport']

logger = logging.getLogger('msnp2p:transport')

class BaseP2PTransport(gobject.GObject):
    __gsignals__ = {
            "chunk-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "chunk-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "blob-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
            }
    
    def __init__(self, client, name, peer):
        gobject.GObject.__init__(self)
        self._client = client
        self._name = name
        self._peer = peer
        self._reset()

    @property
    def name(self):
        return self._name
    
    @property
    def peer(self):
        return self._peer
    
    @property
    def rating(self):
        raise NotImplementedError
    
    @property
    def max_chunk_size(self):
        raise NotImplementedError

    def send(self, blob, callback=None, errback=None):
        if blob.is_control_blob():
            self._control_blob_queue.append(blob)
        else:
            self._data_blob_queue.append(blob)
        self._process_send_queues()

    def register_writable_blob(self, blob):
        if blob.session_id in self._writable_blobs:
            logger.warning("registering already registered blob "\
                    "with session_id=" + str(session_id))
            return
        self._writable_blobs[blob.session_id] = blob

    def _send_chunk(self, chunk):
        raise NotImplementedError

    # Helper methods
    def _reset(self):
        self._writable_blobs = {}
        self._control_blob_queue = []
        self._data_blob_queue = []
        self._pending_ack = {} # blob_id : [blob_offset1, blob_offset2 ...]

    def _add_pending_ack(self, blob_id, chunk_id=0):
        if blob_id not in self._pending_ack:
            self._pending_ack[blob_id] = set()
        self._pending_ack[blob_id].add(chunk_id)

    def _del_pending_ack(self, blob_id, chunk_id=0):
        if blob_id not in self._pending_ack:
            return
        self._pending_ack[blob_id].discard(chunk_id)

        if len(self._pending_ack[blob_id]) == 0:
            del self._pending_ack[blob_id]

    def _on_chunk_received(self, chunk):
        if chunk.require_ack():
            self._send_ack(chunk)

        if chunk.header.flags & TLPFlag.ACK:
            self._del_pending_ack(chunk.header.dw1, chunk.header.dw2)

        #FIXME: handle all the other flags

        if not chunk.is_control_chunk():
            self.emit("chunk-received", chunk)
            session_id = chunk.header.session_id
            if session_id == 0:
                return

            if session_id in self._writable_blobs:
                blob = self._writable_blobs[session_id]

                if chunk.header.blob_offset == 0:
                    blob.id = chunk.header.blob_id

                blob.append_chunk(chunk)
                if blob.is_complete():
                    self.emit("blob-received", blob)
                    del self._writable_blobs[session_id]

        self._process_send_queues()

    def _on_chunk_sent(self, chunk):
        self.emit("chunk-sent", chunk)
        self._process_send_queues()

    def _process_send_queues(self):
        if len(self._control_blob_queue) > 0:
            queue = self._control_blob_queue
        elif len(self._data_blob_queue) > 0:
            queue = self._data_blob_queue
        else:
            return

        blob = queue[0]
        chunk = blob.get_chunk(self.max_chunk_size)
        if blob.is_complete():
            queue.pop(0) # FIXME: we should keep it in the queue until we receive the ACK

        if chunk.require_ack() :
            self._add_pending_ack(chunk.header.blob_id, chunk.header.dw1)
        self._send_chunk(chunk)

    def _send_ack(self, received_chunk):
        flags = received_chunk.header.flags

        flags = TLPFlag.ACK
        if received_chunk.header.flags & TLPFlag.RAK:
            flags |= TLPFlag.RAK

        ack_blob = ControlBlob(0, flags, 
                dw1 = received_chunk.header.blob_id,
                dw2 = received_chunk.header.dw1,
                qw1 = received_chunk.header.blob_size)

        self.send(ack_blob)

gobject.type_register(BaseP2PTransport) 

