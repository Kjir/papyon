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

from papyon.sip.constants import *
from papyon.util.decorator import rw_property

class SDPCodec(object):

    def __init__(self, payload=None, encoding=None, bitrate=None, fmtp=None):
        self.payload = payload
        self.encoding = encoding
        self.bitrate = bitrate
        self.fmtp = fmtp

    def build_rtpmap(self):
        return "%i %s/%i" % (self.payload, self.encoding, self.bitrate)

    def build_fmtp(self):
        return "%i %s" % (self.payload, self.fmtp)

    def parse_rtpmap(self, rtpmap):
        if not rtpmap: return
        payload, codec = rtpmap.split()
        self.payload = int(payload)
        self.encoding = codec.split('/')[0]
        self.bitrate = int(codec.split('/')[1])

    def parse_fmtp(self, fmtp):
        if not fmtp: return
        payload, fmtp = fmtp.split()
        if int(payload) != self.payload: return
        self.fmtp = fmtp

    def __eq__(self, other):
        return (self.payload == other.payload and
                self.encoding == other.encoding and
                self.bitrate == other.bitrate)
                #self.fmtp == other.fmtp)

    def __repr__(self):
        fmtp = ((self.fmtp and (" " + self.fmtp)) or "")
        return "<Codec: %s%s>" % (self.build_rtpmap(), fmtp)


class SDPMedia(object):

    def __init__(self, name, ip=None, port=None, rtcp=None):
        self._attributes = {}
        self._codecs = []
        self._codec = None

        self.name = name
        self.ip = ip
        self.port = port
        self.rtcp = rtcp

    @rw_property
    def rtcp():
        def fget(self):
            return self.get_attribute("rtcp")
        def fset(self, value):
            self.set_attribute("rtcp", value)
        return locals()

    @rw_property
    def codecs():
        def fget(self):
            return self._codecs
        def fset(self, value):
            self._codecs = value
            self.delete_attributes("rtpmap")
            self.delete_attributes("fmtp")
            for codec in value:
                self.add_attribute("rtpmap", codec.build_rtpmap())
                if codec.fmtp:
                    self.add_attribute("fmtp", codec.build_fmtp())
        return locals()

    @property
    def attributes(self):
        return self._attributes

    @property
    def payload_types(self):
        return map(lambda x: str(x.payload), self._codecs)

    def get_codec(self, payload):
        for codec in self._codecs:
            if codec.payload == payload:
                return codec
        return None

    def parse_attribute(self, key, value):
        if key == "rtcp":
            self.rtcp = int(value)
        else:
            if key == "rtpmap":
                codec = SDPCodec()
                codec.parse_rtpmap(value)
                self.codecs.append(codec)
            elif key == "fmtp":
                codec = self.get_codec(int(value.split()[0]))
                if codec:
                    codec.parse_fmtp(value)
            self.add_attribute(key, value)

    def add_attribute(self, key, value):
        self._attributes.setdefault(key, []).append(value)

    def set_attribute(self, key, value):
        self._attributes[key] = [value]

    def get_attributes(self, key):
        return self._attributes.get(key)

    def get_attribute(self, key):
        values = self.get_attributes(key)
        if values is not None:
            return values[0]
        return None

    def delete_attributes(self, key):
        if key in self._attributes:
            del self._attributes[key]

    def __repr__(self):
        return "<SDP Media: %s>" % self.name


class SDPMessage(object):

    def __init__(self):
        self._medias = {}

    @property
    def medias(self):
        return self._medias

    def __str__(self):
        out = []
        out.append("o=- 0 0 IN IP4 %s" % self.medias["audio"].ip)
        out.append("s=session")
        out.append("b=CT:99980")
        out.append("t=0 0")

        for name, media in self._medias.iteritems():
            types = " ".join(media.payload_types)
            out.append("m=%s %s RTP/AVP %s" % (name, media.port, types))
            out.append("c=IN IP4 %s" % media.ip)
            if name == "video":
                out.append("a=x-caps:%s" % VID_XCAPS)
            for k, v in media.attributes.iteritems():
                for value in v:
                    out.append("a=%s:%s" % (k, value))
            out.append("a=encryption:rejected")

        return "\r\n".join(out)

    def parse(self, message):
        media = None

        for line in message.splitlines():
            line = line.strip()
            if not line or line[1] != '=':
                continue
            key = line[0]
            val = line[2:]

            if key == 'm':
                media = SDPMedia(val.split()[0])
                media.port = int(val.split()[1])
                media.rtcp = media.port + 1 # default RTCP port
                self._medias[media.name] = media
            elif key == 'c':
                media.ip = val.split()[2]
            elif key == 'a':
                subkey, val = val.split(':', 1)
                media.parse_attribute(subkey, val)
