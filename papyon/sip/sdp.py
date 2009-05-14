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

from papyon.util.decorator import rw_property

class Codec(object):

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
                self.bitrate == other.bitrate and
                self.fmtp == other.fmtp)

    def __repr__(self):
        fmtp = ((self.fmtp and (" " + self.fmtp)) or "")
        return "<Codec: %s%s>" % (self.build_rtpmap(), fmtp)


class Media(object):

    _attributes = {}
    _codecs = []
    _codec = None

    def __init__(self, name, ip=None, port=None, rtcp=None):
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

    def parse_attribute(self, key, value):
        if key is "rtcp":
            self.rtcp = int(value)
        else:
            if key is "rtpmap":
                self._codec = Codec()
                self._codec.parse_rtpmap(value)
                self._codecs.append(self._codec)
            elif key is "fmtp":
                self._codec.parse_fmtp(value)
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

class Message(object):
    pass
