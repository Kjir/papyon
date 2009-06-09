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
from papyon.util.odict import odict

import logging

logger = logging.getLogger('SDP')

class SDPCodec(object):

    def __init__(self, payload=None, encoding=None, clockrate=None, params=None):
        self.payload = payload
        self.encoding = encoding
        self.clockrate = clockrate
        self.params = params or dict()

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

    @property
    def rtpmap(self):
        if not self.encoding or not self.clockrate:
            return str(self.payload)
        return "%i %s/%i" % (self.payload, self.encoding, self.clockrate)

    @property
    def params_list(self):
        if not self.params:
            return ""
        params = []
        for (key, value) in self.params.items():
            if key == "events":
                params.append("0-16")
            else:
                params.append("%s=%s" % (key, value))
        return " ".join(params)

    @property
    def fmtp(self):
        return "%i %s" % (self.payload, self.params_list)

    def parse_rtpmap(self, rtpmap):
        payload, codec = rtpmap.split()
        self.payload = int(payload)
        self.encoding = codec.split('/')[0]
        self.clockrate = int(codec.split('/')[1])

    def parse_fmtp(self, fmtp):
        params = fmtp.split()
        for param in params[1:]:
            if '=' in param:
                key, value = param.split('=')
            else:
                key = "events"
                value = "0-15"
        self.params[key] = value

    def __eq__(self, other):
        return (self.rtpmap == other.rtpmap and
                self.fmtp == other.fmtp)

    def __repr__(self):
        return "<Codec: %s params={%s}>" % (self.rtpmap, self.params_list)


class SDPMedia(object):

    def __init__(self, name, ip=None, port=None, rtcp=None):
        self._attributes = odict({"encryption": ["rejected"]})
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
                self.add_attribute("rtpmap", codec.rtpmap)
                if codec.params:
                    self.add_attribute("fmtp", codec.fmtp)
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
        for codec in self._codecs:
            if codec.payload == payload:
                return codec
        raise KeyError("No codec with payload %i in media", payload)

    def parse_attribute(self, key, value):
        try:
            if key == "rtcp":
                self.rtcp = int(value)
            else:
                if key == "rtpmap":
                    payload = SDPCodec.get_payload_from_rtpmap(value)
                    codec = self.get_codec(payload)
                    codec.parse_rtpmap(value)
                elif key == "fmtp":
                    payload = SDPCodec.get_payload_from_fmtp(value)
                    codec = self.get_codec(payload)
                    codec.parse_fmtp(value)
                self.add_attribute(key, value)
        except ValueError:
            logger.warning("Invalid %s media attribute (%s)" % (key, value))
        except KeyError:
            logger.warning("Found %s attribute for invalid payload (%i)" %
                    (key, payload))

    def add_attribute(self, key, value=None):
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
        self._medias = []
        self._ip = ""

    @property
    def ip(self):
        if self._ip == "" and len(self._medias) > 1:
            return self._medias[0].ip
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

        for media in self._medias:
            types = " ".join(media.payload_types)
            out.append("m=%s %i RTP/AVP %s" % (media.name, media.port, types))
            out.append("c=IN IP4 %s" % media.ip)
            for (k, v) in media.attributes.items():
                for value in v:
                    out.append("a=%s:%s" % (k, value))

        return "\r\n".join(out) + "\r\n\r\n"

    def parse(self, message):
        media = None

        for line in message.splitlines():
            line = line.strip()
            if not line:
                continue
            if len(line) < 2 or line[1] != '=':
                logger.warning('Invalid line "%s" in message ignored', line)
                continue

            key = line[0]
            val = line[2:]

            try:
                if key == 'o':
                    self._ip = val.split()[5]
                elif key == 'm':
                    media = SDPMedia(val.split()[0])
                    media.port = int(val.split()[1])
                    media.ip = self.ip # default IP address
                    media.rtcp = media.port + 1 # default RTCP port
                    media.payload_types = val.split()[3:]
                    self._medias.append(media)
                elif key == 'c':
                    if media is None:
                        self._ip = val.split()[2]
                    else:
                        media.ip = val.split()[2]
                elif key == 'a':
                    if media is None:
                        continue
                    if ':' in val:
                        subkey, subval = val.split(':', 1)
                        media.parse_attribute(subkey, subval)
                    else:
                        media.add_attribute(val)
            except:
                self._medias = []
                raise ValueError('Invalid value "%s" for field "%s"' % (val, key))

        return self._medias
