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

__all__ = ['MediaSessionMessage', 'MediaDescription']

class MediaSessionMessage(object):

    def __init__(self):
        self._medias = []

    @property
    def medias(self):
        return self._medias

    def create_media_description(self):
        return MediaDescription()


class MediaDescription(object):

    def __init__(self, name, direction):
        self._name = name
        self._direction = direction
        self._codecs = []

    @property
    def name(self):
        return self._name

    @property
    def direction(self):
        return self._direction

    @rw_property
    def codecs():
        def fget(self):
            return self._codecs
        def fset(self, value):
            self._codecs = value
        return locals()

    @property
    def valid_codecs(self):
        return filter(lambda c: self.is_valid_codec(c), self.codecs)

    def is_valid_codec(self, codec):
        return True

    def set_codecs(self, codecs):
        codecs = filter(lambda c: self.is_valid_codec(c), codecs)
        self.codecs = codecs

    def has_active_remote(self):
        return False

    def get_codec(self, payload):
        for codec in self._codecs:
            if codec.payload == payload:
                return codec
        raise KeyError("No codec with payload %i in media", payload)

    def __repr__(self):
        return "<Media Description: %s>" % self.name
