from papyon.event import EventsDispatcher
from papyon.sip.ice import *
from papyon.sip.sdp import *

import gobject
import logging

logger = logging.getLogger('Media')

class MediaSession(gobject.GObject, EventsDispatcher):

    __gsignals__ = {
        'prepared': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'ready': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, tunneled):
        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        self._ice_transport = ICETransport(tunneled)
        self._tunneled = tunneled
        self._streams = []
        self._signals = {}
        self._parsing = False

    @property
    def has_video(self):
        return (self.get_stream("video") is not None)

    @property
    def prepared(self):
        for stream in self._streams:
            if not stream.prepared:
                return False
        if self._parsing:
            return False
        return True

    @property
    def ready(self):
        for stream in self._streams:
            if not stream.ready:
                return False
        return True

    @property
    def tunneled(self):
        return self._tunneled

    def close(self):
        for stream in self._streams:
            self.close_stream(stream)
        del self._streams

    def add_stream(self, name, controlling):
        stream = MediaStream(name, controlling, self._ice_transport)
        sp = stream.connect("prepared", self.on_stream_prepared)
        sr = stream.connect("ready", self.on_stream_ready)
        self._streams.append(stream)
        self._signals[name] = [sp, sr]
        self._dispatch("on_stream_created", stream)
        return stream

    def get_stream(self, name):
        matching = filter(lambda x: x.name == name, self._streams)
        if not matching:
            return None
        else:
            return matching[0]

    def close_stream(self, stream):
        name = stream.name
        for handler_id in self._signals[name]:
            stream.disconnect(handler_id)
        del self._signals[name]
        stream.close()
        self._dispatch("on_stream_removed", stream)

    def build_sdp(self):
        sdp = SDPMessage()
        for stream in self._streams:
            media = stream.build_media()
            sdp.medias.append(media)
        return str(sdp)

    def parse_sdp(self, message, initial=False):
        sdp = SDPMessage()
        self._parsing = True
        try:
            if not sdp.parse(message):
                raise ValueError("SDP message does not contain any media")
            for media in sdp.medias:
                stream = self.get_stream(media.name)
                if stream is None:
                    if initial:
                        stream = self.add_stream(media.name, False)
                    else:
                        raise ValueError('Invalid media "%s" in SDP message' % media.name)
                stream.parse_media(media)
        except Exception, err:
            logger.error(err)
            self._parsing = False
            raise
        self._parsing = False

        if initial and self.ready:
            self.emit("prepared")

    def on_stream_prepared(self, stream):
        if self.prepared:
            self.emit("prepared")

    def on_stream_ready(self, stream):
        if self.ready:
            self.emit("ready")


class MediaStream(gobject.GObject, EventsDispatcher):

    __gsignals__ = {
        'prepared': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'ready': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, name, controlling, transport):
        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        self._name = name
        self._controlling = controlling
        self._transport = transport
        self._local_codecs = []
        self._local_codecs_prepared = False
        self._local_candidate_id = None
        self._local_candidates = []
        self._local_candidates_prepared = False
        self._remote_codecs = []
        self._remote_candidate_id = None
        self._remote_candidates = []

    @property
    def name(self):
        return self._name

    @property
    def controlling(self):
        return self._controlling

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

    def build_media(self):
        ip, port, rtcp = self.get_default_address()
        media = SDPMedia(self._name, ip, port, rtcp)
        media.codecs = self._local_codecs
        self._transport.encode_candidates(self, media)
        return media

    def parse_media(self, media):
        self._remote_codecs = media.codecs
        self._remote_candidates = self._transport.decode_candidates(media)
        if not self._remote_candidates:
            self._remote_candidates = self._transport.get_default_candidates(media)
        self._dispatch("on_remote_codecs_received", self._remote_codecs)
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
        if self._local_codecs_prepared:
            return
        self._local_codecs = codecs
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
