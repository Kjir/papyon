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

class Session(object):
    pass


class Candidate(object):

    def __init__(self, draft=0, foundation=None, component_id=None,
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

    @rw_property
    def type():
        def fget(self):
            return self._extensions.get("typ")
        def fset(self, value):
            self._extensions["typ"] = value
        return locals()

    @rw_property
    def base_ip():
        def fget(self):
            return self._extensions.get("raddr")
        def fset(self, value):
            self._extensions["raddr"] = value
        return locals()

    @rw_property
    def base_port():
        def fget(self):
            return self._extensions.get("rport")
        def fset(self, value):
            self._extensions["rport"] = value
        return locals()

    def build_local(self):
        if self.draft is 6:
            return "%s %i %s %s %.3f %s %i" % (self.username, self.component_id,
                self.password, self.transport, self.priority, self.ip, self.port)
        elif self.draft is 19:
            ext = []
            for k, v in self._extensions.iteritems():
                if v is not None:
                    ext.append("%s %s" % (k, str(v)))
            return "%i %i %s %i %s %i %s" % (self.foundation, self.component_id,
                self.transport, self.priority, self.ip, self.port, " ".join(ext))

    def build_remote(self):
        if self.draft is 6:
            return self.username
        elif self.draft is 19:
            return "%i %s %i" % (self.component_id, self.ip, self.port)

    def parse(self, line):
        parts = line.split()
        parts = map(lambda x: ((x.isdigit() and int(x)) or x), parts)

        if self.draft is 19:
            (self.foundation, self.component_id, self.transport,
                self.priority, self.ip, self.port) = parts[0:6]
            for i in range(6, len(parts), 2):
                self._extensions[parts[i]] = parts[i + 1]
        elif self.draft is 6:
            (self.username, self.component_id, self.password, self.transport,
                self.priority, self.ip, self.port) = parts[0:7]
            self.foundation = self.username[0:31]
            self.priority = float(self.priority)
