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

from papyon.event import EventsDispatcher
from papyon.sip.constants import *
from papyon.sip.ice import *
from papyon.service.SingleSignOn import *

import base64
import gobject
import random
import re
import uuid

class SIPBaseConnection(gobject.GObject):

    __gsignals__ = {
        'invite-received': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ([object])),
        'disconnecting': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'disconnected': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, client, transport):
        gobject.GObject.__init__(self)
        self._calls = {}
        self._client = client
        self._transport = transport
        self._transport.connect("message-received", self.on_message_received)

    @property
    def transport(self):
        return self._transport

    def create_call(self, callid=None):
        call = SIPCall(self, self._client, callid)
        self.add_call(call)
        return call

    def add_call(self, call):
        self._calls[call.id] = call

    def remove_call(self, call):
        if call.id in self._calls:
            del self._calls[call.id]

    def get_call(self, callid):
        return self._calls.get(callid, None)

    def send(self, message, registration=False):
        self._transport.send(message)

    def on_message_received(self, parser, message):
        callid = message.get_header("Call-ID")
        call = self.get_call(callid)
        if call is None:
            if isinstance(message, SIPRequest) and message.code == "INVITE":
                call = self.create_call(callid)
                self.emit("invite-received", call)
            else:
                call = SIPCall(self, self._client, callid)
                response = call.build_response(message, 481)
                call.send(response) # call/transaction does not exist
                return
        call.on_message_received(message)


class SIPConnection(SIPBaseConnection):

    def __init__(self, client, transport):
        SIPBaseConnection.__init__(self, client, transport)
        self._sso = self._client._sso
        self._tokens = {}
        self._msg_queue = []
        self._registration = SIPRegistration(self, self._client)
        self._registration.connect("registered", self.on_registration_success)
        self._registration.connect("unregistered", self.on_unregistration_success)
        self.add_call(self._registration)

    @property
    def registered(self):
        return self._registration.registered

    @property
    def tunneled(self):
        return False

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def register(self, callback, errcb):
        token = self._tokens[LiveService.MESSENGER_SECURE]
        self._registration.register(token)

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def unregister(self, callback, errcb):
        token = self._tokens[LiveService.MESSENGER_SECURE]
        self._registration.unregister(token)
        self.emit("disconnecting")

    def send(self, message, registration=False):
        if self.registered or registration:
            self._transport.send(message)
        else:
            self._msg_queue.append(message)
            self.register(None, None)

    def remove_call(self, call):
        SIPBaseConnection.remove_call(self, call)
        if len(self._calls) == 1:
            self.unregister(None, None)

    def on_registration_success(self, registration):
        while len(self._msg_queue) > 0:
            msg = self._msg_queue.pop(0)
            self.send(msg)

    def on_unregistration_success(self, registration):
        self.emit("disconnected")


class SIPTunneledConnection(SIPBaseConnection):

    @property
    def tunneled(self):
        return True


class SIPBaseCall(gobject.GObject):

    def __init__(self, connection, client, id=None):
        gobject.GObject.__init__(self)
        self._connection = connection
        self._client = client
        self._ip = "127.0.0.1"
        self._port = 50390
        self._transport_protocol = connection.transport.protocol
        self._account = client.profile.account
        self._id = id
        self._cseq = 0
        self._remote = None
        self._route = None
        self._uri = None

    @property
    def id(self):
        if not self._id:
            self._id = uuid.uuid4().get_hex()
        return self._id

    def get_conversation_id(self):
        if self._connection.tunneled:
            return 0
        else:
            return 0

    def get_cseq(self, incr=False):
        if incr:
            self._cseq += 1
        return self._cseq

    def get_epid(self):
        if not hasattr(self, '_epid'):
            self._epid = uuid.uuid4().get_hex()[:10]
        return self._epid

    def get_mepid(self):
        if self._connection.tunneled:
            mepid = self._connection._client.machine_guid
            mepid = filter(lambda c: c not in "{-}", mepid).upper()
            return ";mepid=%s" % mepid
        else:
            return ""

    def get_tag(self):
        if not hasattr(self, '_tag'):
            self._tag = uuid.uuid4().get_hex()
        return self._tag

    def get_sip_instance(self):
        return SIP_INSTANCE

    def send(self, message, registration=False):
        message.call = self
        self._connection.send(message, registration)

    def parse_contact(self, message, name):
        email = self.parse_email(message, name)
        contacts = self._client.address_book.contacts.search_by_account(email)
        if not contacts:
            return None
        return contacts[0]

    def parse_email(self, message, name):
        header = message.get_header(name)
        if header is not None:
            return re.search("<sip:([^;>]*)(;|>)", header).group(1)

    def parse_uri(self, message, name):
        header = message.get_header(name)
        if header is not None:
            return re.search("<sip:([^>]*)>", header).group(1)

    def parse_sip(self, message, name):
        header = message.get_header(name)
        if header is not None:
            return re.search("<sip:[^>]*>", header).group(0)

    def build_from_header(self, name="0"):
        return '"%s" <sip:%s%s>;tag=%s;epid=%s' % \
            (name, self._account, self.get_mepid(), self.get_tag(),
             self.get_epid())

    def build_request(self, code, uri, to, name="0", incr=False):
        request = SIPRequest(code, uri)
        request.add_header("Via", "SIP/2.0/%s %s:%s" %
            (self._transport_protocol, self._ip, self._port))
        request.add_header("Max-Forwards", 70)
        request.add_header("Call-ID", self.id)
        request.add_header("CSeq", "%i %s" % (self.get_cseq(incr), code))
        request.add_header("To", to)
        request.add_header("From", self.build_from_header(name))
        request.add_header("User-Agent", USER_AGENT)
        return request

    def build_response(self, request, status, reason=None):
        response = SIPResponse(status, reason)
        response.clone_headers("From", request)
        response.add_header("To", self.build_from_header())
        response.clone_headers("CSeq", request)
        response.clone_headers("Record-Route", request)
        response.clone_headers("Via", request)
        response.add_header("Call-ID", self.id)
        response.add_header("Max-Forwards", 70)
        response.add_header("User-Agent", USER_AGENT)
        return response

    def on_message_received(self, msg):
        route = self.parse_sip(msg, "Record-Route")
        if route is not None:
            self._route = route
        contact = self.parse_uri(msg, "Contact")
        if contact is not None:
            self._uri = contact

        if type(msg) is SIPResponse:
            self._remote = msg.get_header("To")
            handler_name = "on_%s_response" % msg.code.lower()
        elif type(msg) is SIPRequest:
            self._remote = msg.get_header("From")
            handler_name = "on_%s_received" % msg.code.lower()
        handler = getattr(self, handler_name, None)
        if handler is not None:
            handler(msg)


class SIPCall(SIPBaseCall, EventsDispatcher):

    def __init__(self, connection, client, id=None):
        SIPBaseCall.__init__(self, connection, client, id)
        EventsDispatcher.__init__(self)
        if id is None:
            self._incoming = False
        else:
            self._incoming = True
        if connection.tunneled:
            draft = 19
        else:
            draft = 6
        self._answered = False
        self._early = False
        self._state = None
        self._contact = None
        self._ice = ICESession(["audio"], draft=draft)
        self._ice.connect("candidates-prepared", self.on_candidates_prepared)
        self._ice.connect("candidates-ready", self.on_candidates_ready)
        self._invite = None
        self._invite_src = None
        self._response_src = None
        self._end_src = None

    @property
    def contact(self):
        return self._contact

    @property
    def ice(self):
        return self._ice

    def build_invite_contact(self):
        if self._connection.tunneled:
            m = "<sip:%s%s>;proxy=replace;+sip.instance=\"<urn:uuid:%s>\"" % (
                self._account, self.get_mepid(), self.get_sip_instance())
        else:
            m = "<sip:%s:%i;maddr=%s;transport=%s>;proxy=replace" % (
                self._account, self._port, self._ip, self._transport_protocol)
        return m

    def build_invite_request(self, uri, to):
        conversation_id = self.get_conversation_id()
        request = self.build_request("INVITE", uri, to, incr=True)
        request.add_header("Ms-Conversation-ID", "f=%s" % conversation_id)
        request.add_header("Contact", self.build_invite_contact())
        request.set_content(self._ice.build_sdp(), "application/sdp")
        return request

    def invite(self, contact):
        self._contact = contact
        if not self._ice.candidates_prepared:
            return
        self._state = "CALLING"
        self._early = False
        self._uri = contact.account
        self._remote = "<sip:%s>" % self._uri
        self._invite = self.build_invite_request(self._uri, self._remote)
        self.send(self._invite)
        self._invite_src = gobject.timeout_add(10000, self.on_invite_timeout)

    def reinvite(self):
        if self._incoming or not self._ice.candidates_ready:
            return
        self._state = "REINVITING"
        self._invite = self.build_invite_request(self._uri, self._remote)
        self._invite.add_header("Route", self._route)
        self._invite.add_header("Supported", "ms-dialog-route-set-update")
        self.send(self._invite)
        self._invite_src = gobject.timeout_add(10000, self.on_invite_timeout)

    def answer(self, status):
        response = self.build_response(self._invite, status)
        if status == 200:
            response.add_header("Contact", self.build_invite_contact())
            response.set_content(self._ice.build_sdp(), "application/sdp")
        self.send(response)

    def ring(self):
        if self._invite is None or not self._ice.candidates_prepared:
            return
        self.answer(180)
        self._dispatch("on_call_incoming")
        self._resonse_src = gobject.timeout_add(10000, self.on_response_timeout)
        self.accept()

    def accept(self):
        if self._answered:
            return
        gobject.source_remove(self._response_src)
        self._answered = True
        self.answer(200)

    def reject(self, status=603):
        if self._answered:
            return
        gobject.source_remove(self._response_src)
        self._answered = True
        self.answer(status)
        self.end()

    def reaccept(self):
        if not self._ice.candidates_ready:
            return
        self._state = "CONFIRMED"
        self.answer(200)
        self._dispatch("on_call_connected")

    def send_ack(self, response):
        request = self.build_request("ACK", self._uri, self._remote)
        request.add_header("Route", self._route)
        self.send(request)

    def cancel(self):
        if self._state not in ("CALLING", "REINVITING"):
            return
        self._state = "DISCONNECTING"
        request = self.build_request("CANCEL", self._invite.uri, None)
        request.clone_headers("To", self._invite)
        request.clone_headers("Route", self._invite)
        self.send(request)
        self._end_src = gobject.timeout_add(5000, self.on_end_timeout)

    def send_bye(self):
        self._state = "DISCONNECTING"
        request = self.build_request("BYE", self._uri, self._remote, incr=True)
        request.add_header("Route", self._route)
        self.send(request)
        self._end_src = gobject.timeout_add(5000, self.on_end_timeout)

    def end(self):
        if self._invite_src is not None:
            gobject.source_remove(self._invite_src)
        if self._response_src is not None:
            gobject.source_remove(self._response_src)
        if self._end_src is not None:
            gobject.source_remove(self._end_src)
        self._state = "DISCONNECTED"
        self._dispatch("on_call_ended")
        self._connection.remove_call(self)

    def on_invite_received(self, invite):
        self._invite = invite
        self._contact = self.parse_contact(invite, "From")
        self.answer(100)

        if self._state is None:
            self._state = "INCOMING"
            self._ice.parse_sdp(invite.body)
            self._response_src = gobject.timeout_add(10000, self.on_response_timeout)
            self.ring()
        elif self._state == "CONFIRMED":
            self._state = "REINVITED"
            self.reaccept()
        else:
            self.answer(488) # not acceptable here

    def on_candidates_prepared(self, session):
        if self._state is None:
            self.invite(self._contact)
        elif self._state == "INCOMING":
            self.ring()

    def on_candidates_ready(self, session):
        if self._state == "REINVITED":
            self.reaccept()
        elif self._state == "CONFIRMED":
            self.reinvite()

    def on_ack_received(self, ack):
        self._state = "CONFIRMED"

    def on_cancel_received(self, cancel):
        if self._incoming and not self._answered:
            self.reject(487)
        response = self.build_response(cancel, 200)
        self.send(response)
        self.end()

    def on_bye_received(self, bye):
        response = self.build_response(bye, 200)
        self.send(response)
        self.end()

    def on_invite_response(self, response):
        if self._state == "REINVITING":
            return self.on_reinvite_response(response)
        elif self._state != "CALLING":
            return

        self._remote = response.get_header("To")
        if response.status >= 200:
            self.send_ack(response)
            gobject.source_remove(self._invite_src)

        if response.status is 100:
            self._early = True
        elif response.status is 180:
            self._dispatch("on_call_ringing")
        elif response.status is 200:
            self._state = "CONFIRMED"
            self._dispatch("on_call_accepted")
            self._ice.parse_sdp(response.body)
            self.reinvite()
        elif response.status in (408, 480, 486, 487, 504, 603):
            self._dispatch("on_call_rejected", response)
            self.end()
        else:
            self.send_bye()

    def on_reinvite_response(self, response):
        if response.status >= 200:
            self.send_ack(response)
            gobject.source_remove(self._invite_src)

        if response.status in (100, 488):
            pass
        elif response.status is 200:
            self._state = "CONFIRMED"
            self._dispatch("on_call_connected")
        else:
            self.send_bye()

    def on_cancel_response(self, response):
        self.end()

    def on_bye_response(self, response):
        self.end()

    def on_invite_timeout(self):
        self.cancel()
        return False

    def on_response_timeout(self):
        self.reject(408)
        self._dispatch("on_call_missed")
        return False

    def on_end_timeout(self):
        self.end()
        return False


class SIPRegistration(SIPBaseCall):

    __gsignals__ = {
        'registered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'unregistered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([]))
    }

    def __init__(self, connection, client):
        SIPBaseCall.__init__(self, connection, client)
        self._state = "NEW"

    @property
    def registered(self):
        return (self._state == "REGISTERED")

    def build_register_request(self, timeout, auth):
        uri = self._account.split('@')[1]
        to =  "<sip:%s>" % self._account
        request = self.build_request("REGISTER", uri, to, incr=1)
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

    def unregister(self, token):
        gobject.source_remove(self._src)
        auth = "%s:%s" % (self._account, token)
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
        self._body = None
        self._call = None
        self._headers = {}
        self.set_content("")

    @rw_property
    def body():
        def fget(self):
            return self._body
        def fset(self, value):
            self._body = value
        return locals()

    @rw_property
    def call():
        def fget(self):
            return self._call
        def fset(self, value):
            self._call = value
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

    def clone_headers(self, name, other, othername=None):
        if othername is None:
            othername = name
        name = self.normalize_name(name)
        othername = self.normalize_name(othername)
        values = other.get_headers(othername)
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
        'message-parsed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ([object]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.reset()

    def reset(self):
        self._message = None
        self._length = 0
        self._state = "start"
        self._buffer = ""

    def append(self, chunk):
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
            self.emit("message-parsed", self._message)
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

