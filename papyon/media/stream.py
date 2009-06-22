# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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

from papyon.event import EventsDispatcher
from papyon.media.constants import *

import gobject
import logging

logger = logging.getLogger('Media:Stream')

__all__ = ['MediaStream']

class MediaStream(gobject.GObject, EventsDispatcher):

    __gsignals__ = {
        'prepared': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'ready': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, name, direction, created, transport):
        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        self._name = name
        self._active = False
        self._created = created
        self._direction = direction
        self._transport = transport
        self._local_codecs = []
        self._local_codecs_prepared = False
        self._local_candidate_id = None
        self._local_candidates = []
        self._local_candidates_prepared = False
        self._remote_codecs = []
        self._remote_candidate_id = None
        self._remote_candidates = []
        self.relay = None

    @property
    def name(self):
        return self._name

    @property
    def controlling(self):
        return self._created

    @property
    def direction(self):
        return self._direction

    @property
    def prepared(self):
        return (self._local_codecs_prepared and
                self._local_candidates_prepared)

    @property
    def ready(self):
        return (self._local_candidate_id is not None and
                self._remote_candidate_id is not None)

    def close(self):
        self._dispatch("on_stream_closed")

    def build_media(self, media):
        media.ip, media.port, media.rtcp = self.get_default_address()
        media.codecs = self._local_codecs
        self._transport.encode_candidates(self, media)
        return media

    def parse_media(self, media):
        self._remote_codecs = media.codecs
        candidates = self._transport.decode_candidates(media)
        self._remote_candidates.extend(candidates)
        if not self._remote_candidates:
            self._remote_candidates = self._transport.get_default_candidates(media)

        if media.get_attribute("remote-candidates") or\
           media.get_attribute("remote-candidate"):
            self._remote_candidate_id = candidates[0].foundation
        elif self._active:
            self.process()

    def process(self):
        self._active = True
        if self._remote_codecs:
            self._dispatch("on_remote_codecs_received", self._remote_codecs)
        if self._remote_candidates:
            self._dispatch("on_remote_candidates_received", self._remote_candidates)

    def new_local_candidate(self, candidate):
        self._local_candidates.append(candidate)

    def new_active_candidate_pair(self, local, remote):
        print self.name, "LOCAL", local, " REMOTE", remote
        if self.ready:
            return # ignore other candidate pairs
        self._local_candidate_id = local
        self._remote_candidate_id = remote
        self.emit("ready")

    def local_candidates_prepared(self):
        if self._local_candidates_prepared:
            return
        self._local_candidates_prepared = True
        if self.prepared:
            self.emit("prepared")

    def set_local_codecs(self, codecs):
        self._local_codecs = codecs
        if self._local_codecs_prepared:
            return
        self._local_codecs_prepared = True
        if self.prepared:
            self.emit("prepared")

    def get_active_local_candidates(self):
        active = self._local_candidate_id
        candidates = self._local_candidates
        if active:
            return filter(lambda x: (x.foundation == active), candidates)
        return candidates

    def get_active_remote_candidates(self):
        active = self._remote_candidate_id
        candidates = self._remote_candidates
        if active is None:
            return []
        return filter(lambda x: (x.foundation == active), candidates)

    def get_default_address(self):
        ip = None
        port = None
        rtcp = None

        active = self._local_candidate_id
        if not active:
            active = self.search_relay().foundation

        for candidate in self._local_candidates:
            if candidate.foundation == active and \
               candidate.component_id is COMPONENTS.RTP:
                ip = candidate.ip
                port = candidate.port
            if candidate.foundation == active and \
               candidate.component_id is COMPONENTS.RTCP:
                rtcp = candidate.port

        return ip, port, rtcp

    def search_relay(self):
        relay = None
        for candidate in self._local_candidates:
            if candidate.transport != "UDP":
                continue
            if candidate.is_relay():
                return candidate
            if not relay or candidate.priority < relay.priority:
                relay = candidate
        return relay
