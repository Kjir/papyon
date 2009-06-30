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

from papyon.media.session import MediaSession

__all__ = ['MediaCall']

class MediaCall(object):

    def __init__(self, session_type, candidate_encoder_class, session_msg_call):
        self._media_session = MediaSession(session_type,
                candidate_encoder_class, session_msg_call)

        self._signals = []
        self._signals.append(self._media_session.connect("prepared",
                self.on_media_session_prepared))
        self._signals.append(self._media_session.connect("ready",
            self.on_media_session_ready))

    @property
    def media_session(self):
        return self._media_session

    def invite(self):
        pass

    def accept(self):
        pass

    def reject(self):
        pass

    def ring(self):
        pass

    def end(self):
        pass

    def dispose(self):
        for handler_id in self._signals:
            self._media_session.disconnect(handler_id)
        self._media_session.close()

    def on_media_session_prepared(self):
        pass

    def on_media_session_ready(self):
        pass
