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

import pygst
pygst.require('0.10')

import base64
import farsight
import gobject
import gst

audio_codecs = [
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
]

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

media_types = {
    farsight.MEDIA_TYPE_AUDIO : "audio",
    farsight.MEDIA_TYPE_VIDEO : "video"
}

class Conference(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)
        self._local_candidates = {}

    def setup(self, call):
        self._ice = call.ice
        self._ice.connect("remote-ready", self.on_remote_ready)
        self._pipeline = gst.Pipeline()
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)
        self.conference = gst.element_factory_make("fsrtpconference")
        self._pipeline.add(self.conference)

        if self._ice.draft is 19:
            compatibility_mode = 3
        else:
            compatibility_mode = 2

        params = {"stun-ip" : "64.14.48.28", "stun-port" : 3478,
                "compatibility-mode" : compatibility_mode}
        self.session = self.conference.new_session(farsight.MEDIA_TYPE_AUDIO)
        self.session.set_codec_preferences(self.build_codecs())
        self.participant = self.conference.new_participant("")
        self.stream = self.session.new_stream(self.participant, farsight.DIRECTION_BOTH,
                "nice", params)
        self.stream.connect("src-pad-added", self.on_src_pad_added, self._pipeline)
        audiosrc = self.make_audio_source()
        self._pipeline.add(audiosrc)
        audiosrc.get_pad("src").link(self.session.get_property("sink-pad"))
        self._pipeline.set_state(gst.STATE_PLAYING)

    def build_codecs(self):
        codecs = []
        for args in audio_codecs:
            codec = farsight.Codec(*args)
            codecs.append(codec)
        return codecs

    def convert_candidate(self, fscandidate):
        candidate = ICECandidate(draft=self._ice.draft)
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

    def convert_fs_candidates(self, candidates):
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

    def convert_codecs(self, fscodecs):
        codecs = []
        for fscodec in fscodecs:
            codec = SDPCodec()
            codec.payload = fscodec.id
            codec.encoding = fscodec.encoding_name
            codec.bitrate = fscodec.clock_rate
            #codec.fmtp = fmtp
            codecs.append(codec)
        return codecs

    def convert_fs_codecs(self, codecs):
        fscodecs = []
        for codec in codecs:
            fscodec = farsight.Codec(
                codec.payload,
                codec.encoding,
                farsight.MEDIA_TYPE_AUDIO,
                codec.bitrate)
            fscodecs.append(fscodec)
        return fscodecs

    def on_remote_ready(self, ice):
        codecs = self.convert_fs_codecs(self._ice.get_remote_codecs("audio"))
        candidates = self.convert_fs_candidates(self._ice.get_remote_candidates("audio"))
        self.stream.set_remote_codecs(codecs)
        self.stream.set_remote_candidates(candidates)

    def on_bus_message(self, bus, msg):
        ret = gst.BUS_PASS
        if msg.type == gst.MESSAGE_ELEMENT:
            s = msg.structure
            if s.has_name("farsight-error"):
                print "Farsight error :", s["error-msg"]
            if s.has_name("farsight-codecs-changed"):
                ret = gst.BUS_DROP
                type = s["session"].get_property("media-type")
                name = self.get_media_name(type)
                ready = s["session"].get_property("codecs-ready")
                if ready:
                    codecs = s["session"].get_property("codecs")
                    self._ice.set_local_codecs(name, self.convert_codecs(codecs))
            if s.has_name("farsight-new-local-candidate"):
                ret = gst.BUS_DROP
                type = s["stream"].get_property("session").get_property("media-type")
                name = self.get_media_name(type)
                candidate = self.convert_candidate(s["candidate"])
                self._local_candidates.setdefault(name, []).append(candidate)
            if s.has_name("farsight-local-candidates-prepared"):
                ret = gst.BUS_DROP
                type = s["stream"].get_property("session").get_property("media-type")
                name = self.get_media_name(type)
                candidates = self._local_candidates[name]
                self._local_candidates[name] = []
                self._ice.set_local_candidates(name, candidates)
            if s.has_name("farsight-new-active-candidate-pair"):
                ret = gst.BUS_DROP
                type = s["stream"].get_property("session").get_property("media-type")
                name = self.get_media_name(type)
                local = self.convert_candidate(s["local-candidate"])
                remote = self.convert_candidate(s["remote-candidate"])
                self._ice.set_active_candidates(name, local, remote)
        return ret

    def on_src_pad_added(self, stream, pad, codec, pipeline):
        audiosink = gst.element_factory_make("alsasink")
        pipeline.add(audiosink)
        audiosink.set_state(gst.STATE_PLAYING)
        pad.link(audiosink.get_pad("sink"))

    def get_media_name(self, type):
        if type == farsight.MEDIA_TYPE_AUDIO:
            return "audio"
        elif type == farsight.MEDIA_TYPE_VIDEO:
            return "video"

    def make_audio_source(self, name="audiotestsrc"):
        element = gst.element_factory_make(name)
        element.set_property("is-live", True)
        return element

    def make_audio_sink(self, async=False):
        pass

    def make_video_source(self, name="videotestsrc"):
        "Make a bin with a video source in it, defaulting to first webcamera "
        bin = gst.Bin("videosrc")
        src = gst.element_factory_make(name, name)
        bin.add(src)
        colorspace = gst.element_factory_make("ffmpegcolorspace")
        bin.add(colorspace)
        videoscale = gst.element_factory_make("videoscale")
        bin.add(videoscale)
        src.link(colorspace)
        colorspace.link(videoscale)
        bin.add_pad(gst.GhostPad("src", videoscale.get_pad("src")))
        return bin

    def make_video_sink(self, async=False):
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

class IceMock(object):

    def set_local_candidates(self, name, candidates):
        print "CANDIDATES", name
        for candidate in candidates:
            print candidate.foundation, candidate.ip, candidate.component_id

    def set_local_codecs(self, name, codecs):
        print "CODECS", name, codecs

    def set_active_candidates(self, name, local, remote):
        print "ACTIVE", name, local, remote

if __name__ == "__main__":
    ice = IceMock()
    conference = Conference()
    loop = gobject.MainLoop()
    gobject.idle_add(conference.setup, ice)
    loop.run()
