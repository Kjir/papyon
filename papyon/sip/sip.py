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

class SIPConnection(gobject.GObject):

    def __init__(self, transport, user, password):
        gobject.GObject.__init__(self)
        self._calls = {}
        self._parser = MessageParser()
        self._parser.connect("message-received", self.on_message_received)
        self._transport = transport
        self._transport.connect("line-received", self._parser.on_line_received)

    def on_message_received(self, parser, message):
        if not call:
            if isinstance(message, Request) and message.code == "INVITE":
                callid = message.get_header("Call-ID")
                call = SIPCall(self._transport, callid)
                self._calls[callid] = call
            else:
                pass #something's wrong
        call.on_message_received(message)


class SIPBaseCall(object):

    def __init__(self, transport, user, callid=None, tunneled=False):
        self._transport = transport
        self._user = user
        self._callid = callid
        self._tunneled = tunneled
        self._cseq = random.randint(1000, 5000)

    def gen_call_id(self):
        return 400000000 + random.randint(0,2000000)

    def gen_hex(self):
        ret  = ('%04x'%(random.randint(0, 2**10)))[:4]
        ret += ('%04x'%(random.randint(0, 2**10)))[:4]
        return ret

    def gen_mepid(self):
        pass

    def get_call_id(self):
        if not self._callid:
            self._callid = self.gen_call_id()
        return self._callid

    def get_cseq(self, incr=False):
        if incr:
            self._cseq += 1
        return self._cseq

    def get_epid(self):
        if not hasattr(self, '_epid'):
            self._epid = self.gen_hex()
        return self._epid

    def get_mepid(self):
        if not self._tunneled:
            return ""
        if not hasattr(self, '_mepid'):
            self._mepid = self.gen_mepid()
        return ";mepid=%s" % self._mepid

    def get_tag(self):
        if not hasattr(self, '_tag'):
            self._tag = self.gen_hex()
        return self._tag

    def get_local_address(self):
        return (self._transport.ip, self._transport.port)

    def send(self, message):
        self._transport.send(str(message))

    def build_request(self, code, uri=None, to=None, name="", incr=False):
        request = SIPRequest(code, uri)
        request.add_header("Via", "SIP/2.0/%s %s:%s" %
            (self._transport.protocol, self.get_local_address()))
        request.add_header("Max-Forwards", 70)
        request.add_header("Call-ID", self.get_call_id())
        request.add_header("CSeq", "%i %s" % (self.get_cseq(incr), code))
        request.add_header("To", to)
        request.add_header("From", "%s<sip:%s%s>;tag=%s;epid=%s" %
            (name, self._user, self.get_mepid(), self.get_tag(), self.get_epid()))
        request.add_header("User-Agent", USER_AGENT)
        return request

    def build_response(self, request, status, reason=None):
        response = SIPResponse(status, reason)
        for via in request.get_headers("Via"):
            response.add_header("Via", via)
        response.add_header("Max-Forwards", 70)
        response.add_header("From", request.get_header("From"))
        response.add_header("To", request.get_header("To"))
        response.add_header("Call-ID", self.get_call_id())
        response.add_header("CSeq", request.get_header("CSeq"))
        response.add_header("User-Agent", self.USER_AGENT)
        return response

    def on_message_received(self, msg):
        if type(msg) is SIPResponse:
            handler_name = "on_%s_response" % msg.code.lower()
        elif type(msg) is SIPRequest:
            handler_name = "on_%s_received" % msg.code.lower()
        handler = getattr(self, handler_name, None)
        if handler is not None:
            handler(msg)


class SIPCall(SIPBaseCall):

    def invite(self, uri):
        pass

    def accept(self):
        pass

    def reject(self):
        pass

    def send_ack(self):
        pass

    def cancel(self):
        pass

    def send_bye(self):
        pass

    def on_invite_received(self, invite):
        pass

    def on_ack_received(self, ack):
        pass

    def on_cancel_received(self, cancel):
        pass

    def on_bye_received(self, bye):
        pass

    def on_invite_response(self, response):
        pass

    def on_cancel_response(self, response):
        pass

    def on_bye_response(self, response):
        pass


class SIPRegistration(SIPBaseCall):

    __gsignals__ = {
        'registered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'unregistered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([]))
    }

    def __init__(self, transport, user, password, tunneled=False):
        SIPBaseCall.__init__(self, transport, user, None, tunneled)
        self._state = "NEW"
        self._password = password

    @property
    def registered(self):
        return (self._state == "REGISTERED")

    def build_register_request(self, timeout, auth):
        uri = self._user.split('@')[1]
        request = self.build_request("REGISTER", uri, self._user)
        request.add_header("ms-keep-alive", "UAC;hop-hop=yes"
        request.add_header("Contact", "<sip:%s:%s;transport=%s>proxy=replace" %
            (self.get_local_address(), self._transport.protocol))
        request.add_header("Event", "registration")
        request.add_header("Expires", timeout)
        request.add_header("Authorization", "Basic %s" % auth)

    def register(self):
        auth = "msmsgs:RPS_%s" % self._password
        auth = base64.encodestring(auth).replace("\n", "")
        request = self.build_register_request(900, auth)
        self._state = "REGISTERING"
        self.send(request)

    def cancel(self):
        gobject.remove_source(self._src)
        auth = "%s:%s" % (self._user, self._password)
        auth = base64.encodestring(auth).replace("\n", "")
        request = self.build_register_request(0, auth)
        self._state = "UNREGISTERING"
        self.send(request)

    def on_expire(self):
        self.register()
        return False

    def on_register_response(self, response):
        if self._state == "UNREGISTERING":
            self._state = "UNREGISTERED"
            self.emit("unregistered")
        elif self._state != "REGISTERING":
            return # strange !?
        elif response.status is 200:
            self._state = "REGISTERED"
            self.emit("registered")
            timeout = response.get_header("Expires", 30)
            self._src = gobject.timeout_add(timeout * 1000, self.on_expire)
        else:
            self._state = "UNREGISTERED"
            self.emit("failed")


class SIPMessage(object):

    def __init__(self):
        self._headers = {}
        self.set_content("")

    def add_header(self, name, value):
        name = name.lower()
        self._headers.setdefault(name, []).append(value)

    def set_header(self, name, value):
        name = name.lower()
        self._headers[name] = [value]

    def get_headers(self, name, default=None):
        name = name.lower()
        if name not in self._headers and name in COMPACT_HEADERS:
            name = COMPACT_HEADERS.get(name)
        return self._headers.get(name, default)

    def get_header(self, name, dafault=None):
        value = self.get_headers(name, default)
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


class SIPRequest(SIPMessage):

    def __init__(self, code, uri):
        SIPMessage.__init__(self)
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


class SIPResponse(SIPMessage):

    def __init__(self, status, reason=None):
        SIPMessage.__init__(self)
        self._status = status
        if not reason:
            reason = RESPONSE_CODES[status]
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


class SIPMessageParser(gobject.GObject):

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
                self._message = SIPResponse(code, a)
            elif c == self.version:
                self._message = SIPRequest(a, b[4:])
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
