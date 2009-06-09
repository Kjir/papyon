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

import sys
sys.path.insert(0, "")
from papyon.sip.ice import *
from papyon.sip.sdp import *
from papyon.event.media import *

import pygst
pygst.require('0.10')

import base64
import farsight
import gobject
import gst

codecs_definitions = {
    "audio" : [
        (114, "x-msrta", farsight.MEDIA_TYPE_AUDIO, 16000),
        (111, "SIREN", farsight.MEDIA_TYPE_AUDIO, 16000),
        (112, "G7221", farsight.MEDIA_TYPE_AUDIO, 16000),
        (115, "x-msrta", farsight.MEDIA_TYPE_AUDIO, 8000),
        (116, "SIREN", farsight.MEDIA_TYPE_AUDIO, 8000),
        (4, "G723", farsight.MEDIA_TYPE_AUDIO, 8000),
        (8, "PCMA", farsight.MEDIA_TYPE_AUDIO, 8000),
        (0, "PCMU", farsight.MEDIA_TYPE_AUDIO, 8000),
        (97, "RED", farsight.MEDIA_TYPE_AUDIO, 8000),
        (101, "telephone-event", farsight.MEDIA_TYPE_AUDIO, 8000)
    ],
    "video" : [
        (121, "x-rtvc1", farsight.MEDIA_TYPE_VIDEO, 90000),
        (34, "H263", farsight.MEDIA_TYPE_VIDEO, 90000)
    ]
}

types = {
    0 : None,
    farsight.CANDIDATE_TYPE_HOST  : "host",
    farsight.CANDIDATE_TYPE_SRFLX : "srflx",
    farsight.CANDIDATE_TYPE_PRFLX : "prflx",
    farsight.CANDIDATE_TYPE_RELAY : "relay"
}

protos = {
    farsight.NETWORK_PROTOCOL_TCP : "TCP",
    farsight.NETWORK_PROTOCOL_UDP : "UDP"
}

media_names = {
    farsight.MEDIA_TYPE_AUDIO : "audio",
    farsight.MEDIA_TYPE_VIDEO : "video"
}

media_types = {
    "audio" : farsight.MEDIA_TYPE_AUDIO,
    "video" : farsight.MEDIA_TYPE_VIDEO
}


class MediaSessionHandler(MediaSessionEventInterface):

    def __init__(self, session):
        MediaSessionEventInterface.__init__(self, session)
        self._conference = None
        self._handlers = []
        self._setup()

    def _setup(self):
        self._pipeline = gst.Pipeline()
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)
        self._conference = gst.element_factory_make("fsrtpconference")
        self._participant = self._conference.new_participant("")
        self._pipeline.add(self._conference)
        self._pipeline.set_state(gst.STATE_PLAYING)

    def on_stream_created(self, stream):
        handler = MediaStreamHandler(stream)
        handler.setup(self._conference, self._pipeline, self._participant,
                self._client.tunneled)
        self._handlers.append(handler)

    def on_bus_message(self, bus, msg):
        ret = gst.BUS_PASS
        if msg.type == gst.MESSAGE_ELEMENT:
            s = msg.structure
            if s.has_name("farsight-error"):
                print "Farsight error :", s["error-msg"]
            if s.has_name("farsight-codecs-changed"):
                ret = gst.BUS_DROP
                ready = s["session"].get_property("codecs-ready")
                if ready:
                    codecs = s["session"].get_property("codecs")
                    name = media_names[s["session"].get_property("media-type")]
                    stream = self._client.get_stream(name)
                    stream.set_local_codecs(convert_codecs(codecs))
            if s.has_name("farsight-new-local-candidate"):
                ret = gst.BUS_DROP
                name = media_names[s["stream"].get_property("session").get_property("media-type")]
                candidate = convert_candidate(s["candidate"], self._client.tunneled)
                stream = self._client.get_stream(name)
                stream.new_local_candidate(candidate)
            if s.has_name("farsight-local-candidates-prepared"):
                ret = gst.BUS_DROP
                type = s["stream"].get_property("session").get_property("media-type")
                name = media_names[type]
                stream = self._client.get_stream(name)
                stream.local_candidates_prepared()
            if s.has_name("farsight-new-active-candidate-pair"):
                ret = gst.BUS_DROP
                type = s["stream"].get_property("session").get_property("media-type")
                name = media_names[type]
                stream = self._client.get_stream(name)
                local = s["local-candidate"]
                remote = s["remote-candidate"]
                stream.new_active_candidate_pair(local.foundation, remote.foundation)
        return ret


class MediaStreamHandler(MediaStreamEventInterface):

    def __init__(self, stream):
        MediaStreamEventInterface.__init__(self, stream)

    def setup(self, conference, pipeline, participant, tunneled):
        if tunneled:
            compatibility_mode = 3
        else:
            compatibility_mode = 2

        params = {"stun-ip" : "64.14.48.28", "stun-port" : 3478,
                "compatibility-mode" : compatibility_mode,
                "controlling-mode": self._client.controlling}
        media_type = media_types[self._client.name]
        self.fssession = conference.new_session(media_type)
        self.fssession.set_codec_preferences(build_codecs(self._client.name))
        self.fsstream = self.fssession.new_stream(participant,
                farsight.DIRECTION_BOTH, "nice", params)
        self.fsstream.connect("src-pad-added", self.on_src_pad_added, pipeline)
        source = make_source(self._client.name)
        pipeline.add(source)
        source.get_pad("src").link(self.fssession.get_property("sink-pad"))
        pipeline.set_state(gst.STATE_PLAYING)

    def on_stream_closed(self):
        del self.fsstream

    def on_remote_candidates_received(self, candidates):
        candidates = convert_fs_candidates(candidates)
        self.fsstream.set_remote_candidates(candidates)

    def on_remote_codecs_received(self, codecs):
        codecs = convert_fs_codecs(codecs, self._client.name)
        self.fsstream.set_remote_codecs(codecs)

    def on_src_pad_added(self, stream, pad, codec, pipeline):
        sink = make_sink(self._client.name)
        pipeline.add(sink)
        sink.set_state(gst.STATE_PLAYING)
        pad.link(sink.get_pad("sink"))


# Farsight utility functions

def convert_candidate(fscandidate, tunneled):
    if tunneled:
        draft = 19
    else:
        draft = 6
    candidate = ICECandidate(draft=draft)
    candidate.ip = fscandidate.ip
    candidate.port = fscandidate.port
    candidate.foundation = fscandidate.foundation
    candidate.component_id = fscandidate.component_id
    candidate.transport = protos[fscandidate.proto]
    if candidate.draft is 6:
        candidate.priority = float(fscandidate.priority) / 1000
    elif candidate.draft is 19:
        candidate.priority = int(fscandidate.priority)
    candidate.username = fscandidate.username
    candidate.password = fscandidate.password
    candidate.type = types[fscandidate.type]
    candidate.base_ip = fscandidate.base_ip
    candidate.base_port = fscandidate.base_port
    return candidate

def convert_fs_candidates(candidates):
    fscandidates = []
    for candidate in candidates:
        for k,v in protos.iteritems():
            if v == candidate.transport:
                proto = k
        type = 0
        for k,v in types.iteritems():
            if v == candidate.type:
                type = k
        fscandidate = farsight.Candidate()
        fscandidate.foundation = candidate.foundation
        fscandidate.ip = candidate.ip
        fscandidate.port = candidate.port
        fscandidate.component_id = candidate.component_id
        fscandidate.proto = proto
        fscandidate.type = type
        fscandidate.username = candidate.username
        #FIXME
        while True:
            try:
                base64.b64decode(fscandidate.username)
                break
            except:
                fscandidate.username += "="
        fscandidate.password = candidate.password
        while True:
            try:
                base64.b64decode(fscandidate.password)
                break
            except:
                fscandidate.password += "="
        if candidate.draft is 6:
            fscandidate.priority = int(candidate.priority * 1000)
        elif candidate.draft is 19:
            fscandidate.priority = int(candidate.priority)
        fscandidates.append(fscandidate)
    return fscandidates

def build_codecs(type):
    codecs = []
    for args in codecs_definitions[type]:
        codec = farsight.Codec(*args)
        codecs.append(codec)
    return codecs

def convert_codecs(fscodecs):
    codecs = []
    for fscodec in fscodecs:
        codec = SDPCodec()
        codec.payload = fscodec.id
        codec.encoding = fscodec.encoding_name
        codec.bitrate = fscodec.clock_rate
        #codec.fmtp = fmtp
        codecs.append(codec)
    return codecs

def convert_fs_codecs(codecs, name):
    fscodecs = []
    media_type = media_types[name]
    for codec in codecs:
        fscodec = farsight.Codec(
            codec.payload,
            codec.encoding,
            media_type,
            codec.bitrate)
        fscodecs.append(fscodec)
    return fscodecs


# GStreamer utility functions

def make_source(media_name):
    func = globals()["make_%s_source" % media_name]
    return func()

def make_sink(media_name):
    func = globals()["make_%s_sink" % media_name]
    return func()

def make_audio_source(name="audiotestsrc"):
    element = gst.element_factory_make(name)
    element.set_property("is-live", True)
    return element

def make_audio_sink(async=False):
    return gst.element_factory_make("alsasink")

def make_video_source(name="videotestsrc"):
    "Make a bin with a video source in it, defaulting to first webcamera "
    bin = gst.Bin("videosrc")
    src = gst.element_factory_make(name, name)
    src.set_property("is-live", True)
    src.set_property("pattern", 1)
    bin.add(src)
    filter = gst.element_factory_make("capsfilter")
    filter.set_property("caps", gst.Caps("video/x-raw-yuv , width=[300,500] , height=[200,500], framerate=[20/1,30/1]"))
    bin.add(filter)
    src.link(filter)
    videoscale = gst.element_factory_make("videoscale")
    bin.add(videoscale)
    filter.link(videoscale)
    bin.add_pad(gst.GhostPad("src", videoscale.get_pad("src")))
    return bin

def make_video_sink(async=False):
    "Make a bin with a video sink in it, that will be displayed on xid."
    bin = gst.Bin("videosink")
    sink = gst.element_factory_make("ximagesink", "imagesink")
    sink.set_property("sync", async)
    sink.set_property("async", async)
    bin.add(sink)
    colorspace = gst.element_factory_make("ffmpegcolorspace")
    bin.add(colorspace)
    videoscale = gst.element_factory_make("videoscale")
    bin.add(videoscale)
    videoscale.link(colorspace)
    colorspace.link(sink)
    bin.add_pad(gst.GhostPad("sink", videoscale.get_pad("sink")))
    #sink.set_data("xid", xid) #Future work - proper gui place for imagesink ?
    return bin.get_pad("sink")

