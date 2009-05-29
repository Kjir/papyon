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

    @staticmethod
    def get_payload_from_rtpmap(rtpmap):
        if rtpmap is None:
            return -1
        payload, codec = rtpmap.split(' ', 1)
        return int(payload)

    @staticmethod
    def get_payload_from_fmtp(fmtp):
        if fmtp is None:
            return -1
        payload, fmtp = fmtp.split(' ', 1)
        return int(payload)

    def build_rtpmap(self):
        return "%i %s/%i" % (self.payload, self.encoding, self.bitrate)

    def build_fmtp(self):
        return "%i %s" % (self.payload, self.fmtp)

    def parse_rtpmap(self, rtpmap):
        payload, codec = rtpmap.split()
        self.payload = int(payload)
        self.encoding = codec.split('/')[0]
        self.bitrate = int(codec.split('/')[1])

    def parse_fmtp(self, fmtp):
        payload, fmtp = fmtp.split(' ', 1)
        self.fmtp = fmtp

    def __eq__(self, other):
        return (self.payload == other.payload and
                self.encoding == other.encoding and
                self.bitrate == other.bitrate and
                self.fmtp == other.fmtp)

    def __repr__(self):
        if self.fmtp:
            fmtp = " %s" % self.fmtp
        else:
            fmtp = ""
        return "<Codec: %s%s>" % (self.build_rtpmap(), fmtp)


class SDPMedia(object):

    def __init__(self, name, ip=None, port=None, rtcp=None):
        self._attributes = {"encryption": ["rejected"]}
        self._codecs = []

        self.name = name
        self.ip = ip
        self.port = port
        self.rtcp = rtcp

    @property
    def attributes(self):
        return self._attributes

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
                caps = XCAPS[self.name].get(codec.payload, None)
                if caps is not None:
                    self.add_attribute("x-caps", caps)
        return locals()

    @rw_property
    def payload_types():
        def fget(self):
            return map(lambda x: str(x.payload), self._codecs)
        def fset(self, value):
            for payload in value:
                self._codecs.append(SDPCodec(int(payload)))
        return locals()

    def get_codec(self, payload):
        if payload < 0:
            return None
        for codec in self._codecs:
            if codec.payload == payload:
                return codec
        return None

    def parse_attribute(self, key, value):
        if key == "rtcp":
            self.rtcp = int(value)
        else:
            if key == "rtpmap":
                payload = SDPCodec.get_payload_from_rtpmap(value)
                codec = self.get_codec(payload)
                if codec:
                    codec.parse_rtpmap(value)
            elif key == "fmtp":
                payload = SDPCodec.get_payload_from_fmtp(value)
                codec = self.get_codec(payload)
                if codec:
                    codec.parse_fmtp(value)
            self.add_attribute(key, value)

    def add_attribute(self, key, value):
        self._attributes.setdefault(key, []).append(value)

    def set_attribute(self, key, value):
        self._attributes[key] = [value]

    def get_attributes(self, key):
        return self._attributes.get(key, None)

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
        self._ip = ""

    @property
    def ip(self):
        if self._ip == "":
            return self._medias["audio"].ip
        return self._ip

    @property
    def medias(self):
        return self._medias

    def __str__(self):
        out = []
        out.append("v=0")
        out.append("o=- 0 0 IN IP4 %s" % self.ip)
        out.append("s=session")
        out.append("b=CT:99980")
        out.append("t=0 0")

        for name, media in self._medias.iteritems():
            types = " ".join(media.payload_types)
            out.append("m=%s %s RTP/AVP %s" % (name, media.port, types))
            out.append("c=IN IP4 %s" % media.ip)
            for k, v in media.attributes.iteritems():
                for value in v:
                    out.append("a=%s:%s" % (k, value))

        return "\r\n".join(out) + "\r\n\r\n"

    def parse(self, message):
        media = None

        for line in message.splitlines():
            line = line.strip()
            if not line or line[1] != '=':
                continue
            key = line[0]
            val = line[2:]

            if key == 'o':
                self._ip = val.split()[5]
            elif key == 'm':
                media = SDPMedia(val.split()[0])
                media.port = int(val.split()[1])
                media.ip = self.ip # default IP address
                media.rtcp = media.port + 1 # default RTCP port
                media.payload_types = val.split()[3:]
                self._medias[media.name] = media
            elif key == 'c':
                if media is None:
                    self._ip = val.split()[2]
                else:
                    media.ip = val.split()[2]
            elif key == 'a':
                if media is None:
                    continue
                subkey, val = val.split(':', 1)
                media.parse_attribute(subkey, val)
