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
    """A media session represents a conference which may include multiple
       streams (audio, video). A session handler might have to be implemented
       on the client side to react to the adding/removing of streams (e.g. UI
       notification). See L{papyon.media.conference.MediaSessionHandler} for a
       default implementation using Farsight 2.0.

       The 'prepared' and 'ready' signals are meant to be handled by the media
       call. For example, we might need to send a session message to the other
       participants once the session is prepared (i.e. we discovered all local
       candidates and codecs)."""

    __gsignals__ = {
        'prepared': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'ready': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, type, encoder_class, msg_class):
        """Initialize the session

           @param type: Session type
           @type type: L{papyon.media.constants.MediaSessionType}
           @param encoder_class: The candidates encoder class to use (e.g. ICECandidateEncoder)
           @type encoder_class: subclass of L{papyon.media.candidate.MediaCandidateEncoder}
           @param msg_class: The session message class to use (e.g SDPMessage)
           @type msg_class: subclass of L{papyon.media.message.MediaSessionMessage}"""

        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        self._type = type
        self._encoder = encoder_class(type)
        self._msg_class = msg_class

        self._streams = []
        self._pending_streams = []
        self._signals = {}

    @property
    def has_video(self):
        """Whether this session contain a video stream or not
           @rtype: bool"""
        return (self.get_stream("video") is not None)

    @property
    def prepared(self):
        """Are all streams prepared
           @rtype: bool"""
        if self._pending_streams:
            return False
        for stream in self._streams:
            if not stream.prepared:
                return False
        return True

    @property
    def ready(self):
        """Are all streams ready
           @rtype: bool"""
        if self._pending_streams:
            return False
        for stream in self._streams:
            if not stream.ready:
                return False
        return True

    @property
    def type(self):
        """Session type
           @rtype L{papyon.media.constants.MediaSessionType}"""
        return self._type

    def close(self):
        """Close the session and all contained streams."""

        for stream in self._streams[:]:
            self.remove_stream(stream)

    def create_stream(self, name, direction, created_locally=False):
        """Create a new media stream with the given name and direction.
           The created stream need to be added to the session using add_stream
           or add_pending_stream if the call is not ready yet.

           @param name: Name of the stream (e.g. audio, video...)
           @type name: string
           @param direction: Direction of the stream
           @type direction: L{papyon.media.constants.MediaStreamDirection}
           @param created_locally: Created locally (outgoing call)
           @type created_locally: boolean

           @returns the new stream"""

        logger.debug("Create stream %s" % name)
        stream = MediaStream(name, direction, created, self._encoder)
        if not created:
            self._dispatch("on_stream_created", stream)
        return stream

    def add_stream(self, stream):
        """Add a stream to the session and signal it that we are ready to
           handle its signals. If the call is not ready yet, use
           add_pending_stream instead.

           @param stream: Stream to add
           @type stream: L{papyon.media.stream.MediaStream}"""

        sp = stream.connect("prepared", self.on_stream_prepared)
        sr = stream.connect("ready", self.on_stream_ready)
        self._streams.append(stream)
        self._signals[stream.name] = [sp, sr]
        self._dispatch("on_stream_added", stream)
        stream.process()
        return stream

    def get_stream(self, name):
        """Find a stream by its name.

           @param name: Name of the stream to find
           @type name: string"""

        matching = filter(lambda x: x.name == name, self._streams)
        if not matching:
            return None
        else:
            return matching[0]

    def remove_stream(self, stream):
        """Close a stream and remove it from the session.

           @param stream: Stream to remove
           @type stream: L{papyon.media.stream.MediaStream}"""

        name = stream.name
        for handler_id in self._signals[name]:
            stream.disconnect(handler_id)
        del self._signals[name]
        stream.close()
        self._streams.remove(stream)
        self._dispatch("on_stream_removed", stream)

    def add_pending_stream(self, stream):
        """Add a stream to the pending list when the call is not ready yet for
           some reason and we don't want the 'prepared' or 'ready' signals to
           be emitted. For example, if we are parsing a session message, we
           don't want the 'prepared' signal to be emitted immediatly after the
           first stream has been parsed."""

        logger.debug("Add %s stream to pending list" % stream.name)
        self._pending_streams.append(stream)

    def process_pending_streams(self):
        """Process all streams in the pending list."""

        logger.debug("Process all streams in pending list")
        for stream in self._pending_streams:
            self.add_stream(stream)
        self.clear_pending_streams()
        if self.prepared:
            self.emit("prepared")
        if self.ready:
            self.emit("ready")

    def clear_pending_streams(self):
        """Clear the pending list (e.g. an error caused all streams to be
           invalid."""

        self._pending_streams = []

    def set_relay_info(self, relays):
        """Set the relay info on each stream.

           @param relays: List of relays
           @type relays: list of L{papyon.media.MediaRelay}"""

        idx = 0
        for stream in self._pending_streams:
            stream.relays = relays[idx:idx+2]
            idx += 2

    def build_body(self, *args):
        """Create a session message containing all stream descriptions to send
           to the other call participants. (e.g. an SDP message)

           @returns the message body (string)"""

        msg = self._msg_class(*args)
        for stream in self._streams:
            desc = msg.create_stream_description(stream.name)
            stream.build_description(desc)
        return str(msg)

    def parse_body(self, body, initial=False):
        """Parse the received session message and create media streams
           accordingly. The created streams are added to the pending list and
           we need to call process_pending_streams when the call is ready to
           handle the streams signals.

           @param body: Session message body
           @type body: string
           @param initial: Whether or not this is the first message received
           @type initial: boolean"""

        msg = self._msg_class()
        try:
            if not msg.parse(body):
                raise ValueError("Session message does not contain any information")
            for desc in msg.descriptions:
                stream = self.get_stream(desc.name)
                if stream is None:
                    if initial:
                        stream = self.create_stream(desc.name, desc.direction)
                        self.add_pending_stream(stream)
                    else:
                        raise ValueError('Invalid stream "%s" in session message' % desc.name)
                stream.parse_description(desc)
        except Exception, err:
            import traceback
            traceback.print_exc()
            logger.error(err)
            raise
        return msg

    def on_stream_prepared(self, stream):
        if self.prepared:
            logger.debug("All media streams are prepared")
            self.emit("prepared")

    def on_stream_ready(self, stream):
        if self.ready:
            logger.debug("All media streams are ready")
            self.emit("ready")
