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
from papyon.util.encoding import *

import logging

logger = logging.getLogger('ICE')

class ICETransport(object):

    def __init__(self, session_type):
        if session_type is MediaSessionType.TUNNELED_SIP:
            self.draft = 19
        else:
            self.draft = 6

    def encode_candidates(self, stream, media):
        candidates = stream.get_active_local_candidates()
        if candidates:
            if self.draft is 19:
                media.add_attribute("ice-ufrag", candidates[0].username)
                media.add_attribute("ice-pwd", candidates[0].password)
            for candidate in candidates:
                media.add_attribute("candidate", str(candidate))

        candidates = stream.get_active_remote_candidates()
        if candidates:
            if self.draft is 6:
                candidates = candidates[0:1]
            list = [c.get_remote_id() for c in candidates]
            name = (len(list) > 1 and "remote-candidates") or "remote-candidate"
            media.add_attribute(name, " ".join(list))

    def decode_candidates(self, media):
        candidates = []

        ufrag = media.get_attribute("ice-ufrag")
        pwd = media.get_attribute("ice-pwd")
        attributes = media.get_attributes("candidate")

        if ufrag and pwd:
            draft = 19
        else:
            draft = 6

        for attribute in attributes:
            candidate = ICECandidate(draft=draft, username=ufrag, password=pwd)
            try:
                candidate.parse(attribute)
            except:
                logger.warning('Invalid ICE candidate "%s"' % attribute)
            else:
                candidates.append(candidate)

        return candidates

    def get_default_candidates(self, media):
        candidates = []
        candidates.append(ICECandidate(component_id=COMPONENTS.RTP,
            ip=media.ip, port=media.port, transport="UDP", priority=1,
            type="host"))
        candidates.append(ICECandidate(component_id=COMPONENTS.RTCP,
            ip=media.ip, port=media.rtcp, transport="UDP", priority=1,
            type="host"))
        return candidates


class ICECandidate(object):

    REL_EXT = [("typ", "type"), ("raddr", "base_ip"), ("rport", "base_port")]

    def __init__(self, draft=6, foundation=None, component_id=None,
                 transport=None, priority=None, username=None, password=None,
                 type=None, ip=None, port=None, base_ip=None, base_port=None):
        self._extensions = {}

        self.draft = draft
        self.foundation = foundation
        self.component_id = component_id
        self.transport = transport
        self.priority = priority
        self.username = username
        self.password = password
        self.type = type
        self.ip = ip
        self.port = port
        self.base_ip = base_ip
        self.base_port = base_port

        if draft not in (6, 19):
            logger.error("Unsupported ICE draft version (%s)" % draft)

    def is_relay(self):
        if self.draft is 6:
            return (self.priority < 0.5)
        elif self.draft is 19:
            return (self.type == "relay")

    def __str__(self):
        if self.draft is 6:
            priority = float(self.priority) / 1000
            return "%s %i %s %s %.3f %s %i" % (self.username, self.component_id,
                self.password, self.transport, priority, self.ip, self.port)
        elif self.draft is 19:
            ext = []
            for (name, attr) in self.REL_EXT:
                if getattr(self, attr):
                    ext.append("%s %s" % (name, getattr(self, attr)))
            for k, v in self._extensions.iteritems():
                if v is not None:
                    ext.append("%s %s" % (k, str(v)))
            return "%s %i %s %i %s %i %s" % (self.foundation, self.component_id,
                self.transport, self.priority, self.ip, self.port, " ".join(ext))

    def get_remote_id(self):
        if self.draft is 6:
            return self.username
        elif self.draft is 19:
            return "%i %s %i" % (self.component_id, self.ip, self.port)

    def parse(self, line):
        parts = line.split()

        if self.draft is 19:
            (self.foundation, self.component_id, self.transport,
                self.priority, self.ip, self.port) = parts[0:6]
            for i in range(6, len(parts), 2):
                key, val = parts[i:i + 2]
                for (name, attr) in self.REL_EXT:
                    if key == name:
                        setattr(self, attr, val)
                self._extensions[key] = val
        elif self.draft is 6:
            (self.username, self.component_id, self.password, self.transport,
                self.priority, self.ip, self.port) = parts[0:7]
            self.foundation = self.username[0:32]

        if self.draft is 19:
            self.priority = int(self.priority)
        if self.draft is 6:
            self.priority = int(float(self.priority) * 1000)
        self.component_id = int(self.component_id)
        self.username = fix_b64_padding(self.username)
        self.password = fix_b64_padding(self.password)
        self.port = int(self.port)
        if self.base_port is not None:
            self.base_port = int(self.base_port)

    def __eq__(self, other):
        return (self.draft == other.draft and
                self.foundation == other.foundation and
                self.component_id == other.component_id and
                self.transport == other.transport and
                self.priority == other.priority and
                self.username == other.username and
                self.password == other.password and
                self.type == other.type and
                self.ip == other.ip and
                self.port == other.port and
                self.base_ip == other.base_ip and
                self.base_port == other.base_port)

    def __repr__(self):
        return "<ICE Candidate: %s>" % self
