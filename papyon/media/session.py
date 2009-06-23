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
from papyon.media.stream import *

import gobject
import logging

logger = logging.getLogger('Media:Session')

__all__ = ['MediaSession']

class MediaSession(gobject.GObject, EventsDispatcher):

    __gsignals__ = {
        'prepared': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'ready': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, type, transport_class, msg_class):
        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        self._type = type
        self._transport = transport_class(type)
        self._msg_class = msg_class

        self._streams = []
        self._pending_streams = []
        self._signals = {}

    @property
    def has_video(self):
        return (self.get_stream("video") is not None)

    @property
    def prepared(self):
        if self._pending_streams:
            return False
        for stream in self._streams:
            if not stream.prepared:
                return False
        return True

    @property
    def ready(self):
        for stream in self._streams:
            if not stream.ready:
                return False
        return True

    @property
    def type(self):
        return self._type

    def close(self):
        for stream in self._streams[:]:
            self.remove_stream(stream)

    def create_stream(self, name, direction, created=False):
        stream = MediaStream(name, direction, created, self._transport)
        if not created:
            self._dispatch("on_stream_created", stream)
        return stream

    def add_stream(self, stream):
        sp = stream.connect("prepared", self.on_stream_prepared)
        sr = stream.connect("ready", self.on_stream_ready)
        self._streams.append(stream)
        self._signals[stream.name] = [sp, sr]
        self._dispatch("on_stream_added", stream)
        stream.process()
        return stream

    def get_stream(self, name):
        matching = filter(lambda x: x.name == name, self._streams)
        if not matching:
            return None
        else:
            return matching[0]

    def remove_stream(self, stream):
        name = stream.name
        for handler_id in self._signals[name]:
            stream.disconnect(handler_id)
        del self._signals[name]
        stream.close()
        self._streams.remove(stream)
        self._dispatch("on_stream_removed", stream)

    def add_pending_stream(self, stream):
        logger.debug("Add %s stream to pending list" % stream.name)
        self._pending_streams.append(stream)

    def process_pending_streams(self):
        logger.debug("Process all streams in pending list")
        for stream in self._pending_streams:
            self.add_stream(stream)
        self.clear_pending_streams()
        if self.prepared:
            self.emit("prepared")

    def clear_pending_streams(self):
        self._pending_streams = []

    def set_relay_info(self, relays):
        idx = 0
        for stream in self._pending_streams:
            stream.relays = relays[idx:idx+2]
            idx += 2

    def build_body(self, *args):
        msg = self._msg_class(*args)
        for stream in self._streams:
            media = msg.create_media_description(stream.name)
            stream.build_media(media)
        return str(msg)

    def parse_body(self, body, initial=False):
        msg = self._msg_class()
        try:
            if not msg.parse(body):
                raise ValueError("Session message does not contain any information")
            for media in msg.medias:
                stream = self.get_stream(media.name)
                if stream is None:
                    if initial:
                        stream = self.create_stream(media.name, media.direction)
                        self.add_pending_stream(stream)
                    else:
                        raise ValueError('Invalid media "%s" in session message' % media.name)
                stream.parse_media(media)
        except Exception, err:
            logger.error(err)
            raise
        return msg

    def on_stream_prepared(self, stream):
        if self.prepared:
            self.emit("prepared")

    def on_stream_ready(self, stream):
        if self.ready:
            self.emit("ready")
