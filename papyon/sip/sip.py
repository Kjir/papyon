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

import gobject

class Connection(object):
    pass

class Call(object):
    pass


class Message(object):

    def __init__(self):
        self._headers = {}
        self.set_content("")

    def add_header(self, name, value):
        name = name.lower()
        self._headers.setdefault(name, []).append(value)

    def set_header(self, name, value):
        name = name.lower()
        self._headers[name] = [value]

    def get_headers(self, name):
        name = name.lower()
        if name not in self._headers:
            name = SHORT_HEADERS.get(name)
        return self._headers.get(name)

    def get_header(self, name):
        value = self.get_headers(name)
        if type(value) == list:
            return value[0]
        return value

    def set_content(self, content, type=None):
        if type:
            self.set_header("Content-Type", type)
        self.set_header("Content-Length", len(content))
        self._body = content

    def get_content(self):
        return self._body

    def get_header_line(self):
        raise NotImplementedError

    def __str__(self):
        s = [self.get_header_line()]
        for k, v in self._headers.items():
            for value in v:
                s.append("%s: %s" % (k, value))
        s.append("")
        s.append(self._body)
        return "\r\n".join(s)


class Request(Message):

    def __init__(self, code, uri):
        Message.__init__(self)
        self._code = code
        self._uri = uri

    @property
    def code(self):
        return self._code

    @property
    def uri(self):
        return self._uri

    def get_header_line(self):
        return "%s sip:%s SIP/2.0" % (self._code, self._uri)

    def __repr__(self):
        return "<SIP Request %d:%s %s>" % (id(self), self._code, self._uri)


class Response(Message):

    def __init__(self, status, reason=None):
        Message.__init__(self)
        self._status = status
        if not reason:
            reason = MESSAGE_TYPES[status]
        self._reason = reason

    @property
    def code(self):
        cseq = self.get_header("CSeq")
        if not cseq:
            return None
        return cseq.split()[1]

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    def get_header_line(self):
        return "SIP/2.0 %s %s" % (self._status, self._reason)

    def __repr__(self):
        return "<SIP Response %d:%s %s>" % (id(self), self._status, self._reason)


class MessageParser(gobject.GObject):

    version = "SIP/2.0"

    __gsignals__ = {
        'message-received': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ([object]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.reset()

    def reset(self):
        self._message = None
        self._length = 0
        self._state = "start"

    def on_line_received(self, transport, line):
        if self._state == "start":
            a, b, c = line.split(" ", 2)
            if a == self.version:
                code = int(b)
                self._message = Response(code, a)
            elif c == self.version:
                self._message = Request(a, b[4:])
            self._state = "headers"
        elif self._state == "headers":
            if line:
                name, value = line.split(":", 1)
                self._message.add_header(name, value.strip())
            else:
                self._length = int(self._message.get_header("Content-Length"))
                if self._length > 0:
                    self._state = "body"
                else:
                    self._state = "done"
        elif self._state == "body":
            self._message.body += "%s\r\n" % line
            if len(self._message.body) >= self._length:
                self._state = "done"

        if self._state == "done":
            self.emit("message-received", self._message)
            self.reset()
