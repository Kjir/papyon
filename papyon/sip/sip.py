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
from papyon.sip.ice import *
from papyon.service.SingleSignOn import *

import base64
import gobject
import random
import re

class SIPBaseConnection(gobject.GObject):

    __gsignals__ = {
        'invite-received': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ([object]))
    }

    def __init__(self, transport, account):
        gobject.GObject.__init__(self)
        self._calls = {}
        self._transport = transport
        self._account = account
        self._parser = SIPMessageParser(transport)
        self._parser.connect("message-received", self.on_message_received)

    @property
    def transport(self):
        return self._transport

    def create_call(self, callid=None, tunneled=False):
        call = SIPCall(self, self._account, callid, tunneled)
        self.add_call(call)
        return call

    def add_call(self, call):
        self._calls[call.get_call_id()] = call

    def get_call(self, callid):
        return self._calls.get(callid, None)

    def send(self, message):
        self._transport.send(str(message))

    def on_message_received(self, parser, message):
        callid = message.get_header("Call-ID")
        call = self.get_call(callid)
        if call is None:
            if isinstance(message, SIPRequest) and message.code == "INVITE":
                call = self.create_call(callid)
                self.emit("invite-received", call)
            else:
                return #something's wrong
        call.on_message_received(message)


class SIPConnection(SIPBaseConnection):

    def __init__(self, transport, sso, account, password):
        SIPBaseConnection.__init__(self, transport, account)
        self._account = account
        self._password = password
        self._sso = sso
        self._tokens = {}
        self._msg_queue = []
        self._registration = SIPRegistration(self, account, password)
        self._registration.connect("registered", self.on_registration_success)
        self.add_call(self._registration)

    @property
    def registered(self):
        return self._registration.registered

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def register(self, callback=None, errcb=None):
        token = self._tokens[LiveService.MESSENGER_SECURE]
        self._registration.register(token)

    def invite(self, uri):
        call = self.create_call()
        call.invite(uri)
        return call

    def send(self, message, registration=False):
        if self.registered or registration:
            self._transport.send(str(message))
        else:
            self._msg_queue.append(message)
            self.register(None, None)

    def on_registration_success(self, registration):
        while len(self._msg_queue) > 0:
            msg = self._msg_queue.pop()
            self.send(msg)


class SIPBaseCall(gobject.GObject):

    def __init__(self, connection, account, callid=None, tunneled=False):
        gobject.GObject.__init__(self)
        self._connection = connection
        self._ip = "127.0.0.1"
        self._port = 50390
        self._transport_protocol = connection.transport.protocol
        self._account = account
        self._callid = callid
        self._tunneled = tunneled
        self._cseq = random.randint(1000, 5000)
        self._uri = None

    def gen_call_id(self):
        return str(400000000 + random.randint(0,2000000))

    def gen_hex(self):
        ret  = ('%04x'%(random.randint(0, 2**10)))[:4]
        ret += ('%04x'%(random.randint(0, 2**10)))[:4]
        return ret

    def gen_mepid(self):
        # TODO generate a machine guid
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

    def get_sip_instance(self):
        return SIP_INSTANCE

    def send(self, message, registration=False):
        self._connection.send(message, registration)

    def build_request(self, code, uri, to, name="0", incr=False):
        request = SIPRequest(code, uri)
        request.add_header("Via", "SIP/2.0/%s %s:%s" %
            (self._transport_protocol, self._ip, self._port))
        request.add_header("Max-Forwards", 70)
        request.add_header("Call-ID", self.get_call_id())
        request.add_header("CSeq", "%i %s" % (self.get_cseq(incr), code))
        request.add_header("To", to)
        request.add_header("From", "\"%s\" <sip:%s%s>;tag=%s;epid=%s" %
            (name, self._account, self.get_mepid(), self.get_tag(),
             self.get_epid()))
        request.add_header("User-Agent", USER_AGENT)
        return request

    def build_response(self, request, status, reason=None):
        to = request.get_header("To")
        if not "tag=" in to:
            to += ";tag=" + self.get_tag()

        response = SIPResponse(status, reason)
        response.clone_headers("From", request)
        response.add_header("To", to)
        response.clone_headers("CSeq", request)
        response.clone_headers("Record-Route", request)
        response.clone_headers("Via", request)
        response.add_header("Call-ID", self.get_call_id())
        response.add_header("Max-Forwards", 70)
        response.add_header("User-Agent", USER_AGENT)
        return response

    def on_message_received(self, msg):
        route = msg.get_header("Record-Route")
        if route is not None:
            self._uri = re.search("<sip:(.*)>", route).group(1)
        contact = msg.get_header("Contact")
        if contact is not None:
            self._contact = re.search("<sip:.*>", contact).group(0)

        if type(msg) is SIPResponse:
            handler_name = "on_%s_response" % msg.code.lower()
        elif type(msg) is SIPRequest:
            handler_name = "on_%s_received" % msg.code.lower()
        handler = getattr(self, handler_name, None)
        if handler is not None:
            handler(msg)


class SIPCall(SIPBaseCall):

    def __init__(self, connection, account, callid=None, tunneled=False):
        SIPBaseCall.__init__(self, connection, account, callid, tunneled)
        self._state = None
        self._ice = ICESession(["audio"], draft=6)
        self._ice.connect("candidates-prepared", self.on_candidates_prepared)
        self._ice.connect("candidates-ready", self.on_candidates_ready)

    @property
    def ice(self):
        return self._ice

    def build_invite_contact(self):
        if self._tunneled:
            m = "<sip:%s%s>;proxy=replace;+sip.instance=\"<urn:uuid:%s>\"" % (
                self._account, self.get_mepid(), self.get_sip_instance())
        else:
            m = "<sip:%s:%i;maddr=%s;transport=%s>;proxy=replace" % (
                self._account, self._port, self._ip, self._transport_protocol)
        return m

    def build_invite_request(self, uri, to):
        request = self.build_request("INVITE", uri, to, incr=True)
        request.add_header("Ms-Conversation-ID", "f=%s" % int(self._tunneled))
        request.add_header("Contact", self.build_invite_contact())
        request.add_header("Record-Route", "<sip:127.0.0.1:50930;transport=tcp>")
        request.set_content(self._ice.build_sdp(), "application/sdp")
        return request

    def invite(self, uri):
        self._uri = uri
        if not self._ice.candidates_prepared:
            return
        self._state = "CALLING"
        self._remote = "<sip:%s>" % uri
        self._invite = self.build_invite_request(uri, self._remote)
        self.send(self._invite)

    def reinvite(self):
        if not self._ice.candidates_ready:
            return
        self._state = "REINVITING"
        self._invite = self.build_invite_request(self._uri, self._remote)
        self._invite.add_header("Route", self._contact)
        self._invite.add_header("Supported", "ms-dialog-route-set-update")
        self.send(self._invite)

    def accept(self):
        response = self.build_response(self._invite, 200)
        response.add_header("Contact", self.build_invite_contact())
        response.set_content(self._ice.build_sdp(), "application/sdp")
        self.send(response)

    def reject(self, status=603):
        response = self.build_response(self._invite, status)
        response.add_header("Contact", self.build_invite_contact())
        self.send(response)

    def send_ack(self, response):
        to = response.get_header("To")
        request = self.build_request("ACK", self._uri, to)
        self.send(request)

    def cancel(self):
        if self._state != "CALLING":
            return
        self._state = "DISCONNECTING"
        uri = self._invite.uri
        to = self._invite.get_header("To")
        request = self.build_request("CANCEL", uri, to)
        self.send(request)

    def send_bye(self):
        self._state = "DISCONNECTING"
        request = self.build_request("BYE", self._uri, self._remote, incr=True)
        self.send(request)

    def on_invite_received(self, invite):
        self._invite = invite
        self._remote = invite.get_header("From")
        self._ice.parse_sdp(invite.body)
        ringing = self.build_response(invite, 180)
        self.send(ringing)

        if self._state == "CONFIRMED":
            if self._ice.candidates_ready:
                self.accept()
            else:
                self._state = "REINVITED"
        else:
            self._state = "INCOMING"

    def on_candidates_prepared(self, session):
        if self._state is None:
            self.invite(self._uri)
        elif self._state == "INCOMING":
            pass

    def on_candidates_ready(self, session):
        if self._state == "REINVITED":
            self.accept()
        elif self._state == "CONFIRMED":
            self.reinvite()

    def on_ack_received(self, ack):
        self._state = "CONFIRMED"

    def on_cancel_received(self, cancel):
        if self._state == "INVITED":
            self.reject(487)
        self._state = "DISCONNECTED"
        response = self.build_response(cancel, 200)
        self.send(response)

    def on_bye_received(self, bye):
        self._state = "DISCONNECTED"
        response = self.build_response(bye, 200)
        self.send(response)

    def on_invite_response(self, response):
        old_state = self._state
        self._remote = response.get_header("To")
        if response.status >= 200:
            self.send_ack(response)

        if response.status in (100, 180, 408, 480, 486, 487, 504, 603):
            pass
        elif response.status is 200:
            self._state = "CONFIRMED"
            self._ice.parse_sdp(response.body)
            if old_state == "CALLING":
                self.reinvite()
        else:
            self.send_bye()

    def on_cancel_response(self, response):
        self._state = "DISCONNECTED"

    def on_bye_response(self, response):
        if response.status in (200, 403):
            self._state = "DISCONNECTED"
        else:
            pass #self.send_bye()


class SIPRegistration(SIPBaseCall):

    __gsignals__ = {
        'registered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'unregistered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([]))
    }

    def __init__(self, connection, account, password, tunneled=False):
        SIPBaseCall.__init__(self, connection, account, None, tunneled)
        self._state = "NEW"
        self._password = password

    @property
    def registered(self):
        return (self._state == "REGISTERED")

    def build_register_request(self, timeout, auth):
        uri = self._account.split('@')[1]
        request = self.build_request("REGISTER", uri, "<sip:%s>" % self._account)
        request.add_header("ms-keep-alive", "UAC;hop-hop=yes")
        request.add_header("Contact", "<sip:%s:%s;transport=%s>;proxy=replace" %
            (self._ip, self._port, self._transport_protocol))
        request.add_header("Event", "registration")
        request.add_header("Expires", timeout)
        request.add_header("Authorization", "Basic %s" % auth)
        return request

    def register(self, ticket):
        auth = "msmsgs:RPS_%s" % ticket
        auth = base64.b64encode(auth).replace("\n", "")
        request = self.build_register_request(900, auth)
        self._state = "REGISTERING"
        self.send(request, True)

    def cancel(self):
        gobject.remove_source(self._src)
        auth = "%s:%s" % (self._account, self._password)
        auth = base64.encodestring(auth).replace("\n", "")
        request = self.build_register_request(0, auth)
        self._state = "UNREGISTERING"
        self.send(request, True)

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
            timeout = int(response.get_header("Expires", 30))
            self._src = gobject.timeout_add(timeout * 1000, self.on_expire)
        else:
            self._state = "UNREGISTERED"
            self.emit("failed")


class SIPMessage(object):

    def __init__(self):
        self._headers = {}
        self.set_content("")

    @rw_property
    def body():
        def fget(self):
            return self._body
        def fset(self, value):
            self._body = value
        return locals()

    @property
    def length(self):
        return int(self.get_header("Content-Length", 0))

    def normalize_name(self, name):
        name = name.lower()
        if len(name) is 1:
            for long, compact in COMPACT_HEADERS.iteritems():
                if name == compact:
                    return long
        return name

    def add_header(self, name, value):
        name = self.normalize_name(name)
        if name in UNIQUE_HEADERS:
            self._headers[name] = [value]
        else:
            self._headers.setdefault(name, []).append(value)

    def set_header(self, name, value):
        name = self.normalize_name(name)
        self._headers[name] = [value]

    def get_headers(self, name, default=None):
        name = self.normalize_name(name)
        return self._headers.get(name, default)

    def get_header(self, name, default=None):
        value = self.get_headers(name, default)
        if type(value) == list:
            return value[0]
        return value

    def clone_headers(self, name, other):
        name = self.normalize_name(name)
        values = other.get_headers(name)
        if values is not None:
            self._headers[name] = values

    def set_content(self, content, type=None):
        if type:
            self.set_header("Content-Type", type)
        self.set_header("Content-Length", len(content))
        self._body = content

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

    def __init__(self, transport):
        gobject.GObject.__init__(self)
        transport.connect("chunk-received", self.on_chunk_received)
        self.reset()

    def reset(self):
        self._message = None
        self._length = 0
        self._state = "start"
        self._buffer = ""

    def on_chunk_received(self, transport, chunk):
        self._buffer += chunk
        finished = False
        while not finished:
            finished = self.parse_buffer()

    def parse_buffer(self):
        if self._state == "start":
            line = self.consume_line()
            if line is None:
                return True
            a, b, c = line.split(" ", 2)
            if a == self.version:
                code = int(b)
                self._message = SIPResponse(code, a)
            elif c == self.version:
                self._message = SIPRequest(a, b[4:])
            self._state = "headers"

        if self._state == "headers":
            line = self.consume_line()
            if line is None:
                return True
            elif line == "":
                self._state = "body"
            else:
                name, value = line.split(":", 1)
                self._message.add_header(name, value.strip())

        if self._state == "body":
            missing = self._message.length - len(self._message.body)
            self._message.body += self.consume_chars(missing)
            if len(self._message.body) >= self._message.length:
                self._state = "done"
            else:
                return True

        if self._state == "done":
            self.emit("message-received", self._message)
            self.reset()
            return True

        return False

    def consume_line(self):
        try:
            line, self._buffer = self._buffer.split("\r\n", 1)
        except:
            return None
        return line

    def consume_chars(self, count):
        if count is 0:
            ret = ""
        elif count >= len(self._buffer):
            ret = self._buffer
            self._buffer = ""
        else:
            ret = self._buffer[0:count]
            self._buffer = self._buffer[count:]
        return ret

