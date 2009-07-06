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

from papyon.media import MediaCandidate, MediaCandidateEncoder, MediaSessionType
from papyon.media.constants import *
from papyon.util.encoding import *

import logging

logger = logging.getLogger('ICE')

class ICECandidateEncoder(MediaCandidateEncoder):

    def __init__(self, session_type):
        MediaCandidateEncoder.__init__(self, session_type)
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
                attribute = ICECandidateBuilder.build_candidate(self.draft, candidate)
                media.add_attribute("candidate", attribute)

        candidates = stream.get_active_remote_candidates()
        if candidates:
            if self.draft is 6:
                candidates = candidates[0:1]
            list = [ICECandidateBuilder.build_remote_id(self.draft, candidate) \
                    for candidate in candidates]
            name = (len(list) > 1 and "remote-candidates") or "remote-candidate"
            media.add_attribute(name, " ".join(list))

    def decode_candidates(self, media):
        candidates = []

        ufrag = media.get_attribute("ice-ufrag")
        pwd = media.get_attribute("ice-pwd")
        attributes = media.get_attributes("candidate")

        if attributes is None:
            return candidates

        if ufrag and pwd:
            draft = 19
        else:
            draft = 6

        for attribute in attributes:
            candidate = MediaCandidate(username=ufrag, password=pwd)
            try:
                ICECandidateParser.parse(draft, candidate, attribute)
            except:
                logger.warning('Invalid ICE candidate "%s"' % attribute)
            else:
                candidates.append(candidate)

        return candidates

    def get_default_candidates(self, media):
        candidates = []
        candidates.append(MediaCandidate(component_id=COMPONENTS.RTP,
            ip=media.ip, port=media.port, transport="UDP", priority=1,
            type="host"))
        candidates.append(MediaCandidate(component_id=COMPONENTS.RTCP,
            ip=media.ip, port=media.rtcp, transport="UDP", priority=1,
            type="host"))
        return candidates


REL_EXT = [("typ", "type"), ("raddr", "base_ip"), ("rport", "base_port")]

class ICECandidateBuilder(object):

    @staticmethod
    def build_candidate(draft, cand):
        if draft is 6:
            priority = float(cand.priority) / 1000
            return "%s %i %s %s %.3f %s %i" % (cand.username, cand.component_id,
                cand.password, cand.transport, priority, cand.ip, cand.port)
        elif draft is 19:
            ext = []
            for (name, attr) in REL_EXT:
                if getattr(cand, attr):
                    ext.append("%s %s" % (name, getattr(cand, attr)))
            return "%s %i %s %i %s %i %s" % (cand.foundation, cand.component_id,
                cand.transport, cand.priority, cand.ip, cand.port, " ".join(ext))

    @staticmethod
    def build_remote_id(draft, cand):
        if draft is 6:
            return cand.username
        elif draft is 19:
            return "%i %s %i" % (cand.component_id, cand.ip, cand.port)


class ICECandidateParser(object):

    @staticmethod
    def parse(draft, cand, line):
        parts = line.split()

        if draft is 19:
            (cand.foundation, cand.component_id, cand.transport,
                cand.priority, cand.ip, cand.port) = parts[0:6]
            for i in range(6, len(parts), 2):
                key, val = parts[i:i + 2]
                for (name, attr) in REL_EXT:
                    if key == name:
                        setattr(cand, attr, val)
        elif draft is 6:
            (cand.username, cand.component_id, cand.password, cand.transport,
                cand.priority, cand.ip, cand.port) = parts[0:7]
            cand.foundation = cand.username[0:32]

        if draft is 19:
            cand.priority = int(cand.priority)
            cand.relay = (cand.priority < 0.5)
        if draft is 6:
            cand.priority = int(float(cand.priority) * 1000)
            cand.relay = (cand.type == "relay")

        cand.component_id = int(cand.component_id)
        cand.username = fix_b64_padding(cand.username)
        cand.password = fix_b64_padding(cand.password)
        cand.port = int(cand.port)
        if cand.base_port is not None:
            cand.base_port = int(cand.base_port)
