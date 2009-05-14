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

class Media(object):
    pass

class Message(object):
    pass
