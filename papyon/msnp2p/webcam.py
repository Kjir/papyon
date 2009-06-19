# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2008 Richard Spiers <richard.spiers@gmail.com>
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

from papyon.msnp2p.constants import *
from papyon.msnp2p.SLP import *
from papyon.msnp2p.transport import *
from papyon.msnp2p.exceptions import *
from papyon.msnp2p.session import P2PSession
from papyon.event import EventsDispatcher
from papyon.util.decorator import rw_property
import papyon.util.element_tree as ElementTree
import struct

import papyon.util.guid as guid

import gobject
import base64
import random

from papyon.sip.constants import *
from papyon.sip.ice import *
from papyon.sip.media import *
from papyon.sip.sdp import *

__all__ = ['WebcamSession']

class WebcamSession(P2PSession, EventsDispatcher):

    def __init__(self, producer, session_manager, peer,
            euf_guid,  message = None):
        P2PSession.__init__(self, session_manager, peer, euf_guid,
                ApplicationID.WEBCAM, message)
        EventsDispatcher.__init__(self)

        self._producer = producer
        self._answered = False
        self._sent_syn = False
        self._session_id = self._generate_id(9999)
        self._xml_needed = False
        self._media_session = MediaSession(MediaSessionType.WEBCAM,
                WebcamTransport, WebcamSessionMessage)
        self._media_session.connect("prepared", self._on_media_session_prepared)

    @property
    def media_session(self):
        return self._media_session

    def invite(self):
        self._answered = True
        context = "{B8BE70DE-E2CA-4400-AE03-88FF85B9F4E8}"
        context = context.decode('ascii').encode('utf-16_le')
        self._invite(context)

    def ring(self):
        pass

    def accept(self):
        self._answered = True
        temp_application_id = self._application_id
        self._application_id = 0
        self._respond(200)
        self._application_id = temp_application_id
        self.send_binary_syn()

    def reject(self):
        self._answered = True
        self._respond(603)

    def end(self):
        if not self._answered:
            self.reject()
        else:
            context = '\x74\x03\x00\x81'
            self._close(context)
        self._dispatch("on_call_ended")

    def _on_media_session_prepared(self, session):
        if self._xml_needed:
            self._send_xml()

    def _on_invite_received(self, message):
        if self._producer:
            self._media_session.add_stream("video",
                    MediaStreamDirection.SENDING, False)

    def _on_bye_received(self, message):
        self._dispatch("on_call_ended")
        self._dispose()

    def _on_session_accepted(self):
        self._dispatch("on_call_accepted")

    def _on_session_rejected(self, message):
        self._dispatch("on_call_rejected", message)

    def _on_data_blob_received(self, blob):
        data = blob.data.read()
        data = unicode(data[10:], "utf-16-le").rstrip("\x00")

        if not self._sent_syn:
            self.send_binary_syn() #Send 603 first ?
        if data == 'syn':
            self.send_binary_ack()
        elif data == 'ack' and self._producer:
            self._send_xml()
        elif '<producer>' in data or '<viewer>' in data:
            self._handle_xml(data)

    def send_data(self, data):
        message_bytes = data.encode("utf-16-le") + "\x00\x00"
        id = (self._generate_id() << 8) | 0x80
        header = struct.pack("<LHL", id, 8, len(message_bytes))
        self._send_p2p_data(header + message_bytes)

    def send_binary_syn(self):
        self.send_data('syn')
        self._sent_syn = True

    def send_binary_ack(self):
        self.send_data('ack')

    def send_binary_viewer_data(self):
        self.send_data('receivedViewerData')

    def _send_xml(self):
        if not self._media_session.prepared:
            self._xml_needed = True
            return
        self._xml_needed = False
        body = self.media_session.build_body(self._session_id, self._producer)
        self.send_data(body)

    def _handle_xml(self, data):
        print "Received xml %s" % data
        initial = not self._producer
        msg = self.media_session.parse_body(data, initial)
        self._session_id = msg.id
        if self._producer:
            self.send_binary_viewer_data()
        else:
            self._send_xml()

class WebcamTransport(object):

    def __init__(self, session_type):
        pass

    def encode_candidates(self, stream, media):
        candidates = stream.get_active_local_candidates()
        for candidate in candidates:
            media.ips.append(candidate.ip)
            media.ports.append(candidate.port)
        media.rid = int(candidates[0].foundation)
        media.sid = int(candidates[0].username)

    def decode_candidates(self, media):
        candidates = []
        for ip in media.ips:
            for port in media.ports:
                candidate = ICECandidate()
                candidate.foundation = str(media.rid)
                candidate.component_id = 0
                candidate.username = str(media.sid)
                candidate.ip = ip
                candidate.port = port
                candidate.transport = "TCP"
                candidates.append(candidate)
        return candidates

class WebcamSessionMessage(object):

    def __init__(self, id=0, producer=False):
        self._id = id
        self._producer = producer
        self._medias = []

    @property
    def id(self):
        return self._id

    @property
    def producer(self):
        return self._producer

    @property
    def medias(self):
        return self._medias

    def create_media_description(self, name="video"):
        media = WebcamMediaDescription(self._id, self._producer)
        self._medias.append(media)
        return media

    def parse(self, body):
        tree = ElementTree.fromstring(body)
        self._id = int(tree.find("session").text)
        media = self.create_media_description()
        for node in tree.findall("tcp/*"):
            if node.tag == "tcpport":
                media.ports.append(int(node.text))
            elif node.tag.startswith("tcpipaddress"):
                media.ips.append(node.text)
        media.rid = tree.find("rid").text
        return self._medias

    def __str__(self):
        tag = self.producer and "producer" or "viewer"
        media = self._medias[0]
        body = "<%s>" \
            "<version>2.0</version>" \
            "<rid>%s</rid>" \
            "<session>%u</session>" \
            "<ctypes>0</ctypes>" \
            "<cpu>2010</cpu>" % (tag, media.rid, media.sid)
        body += "<tcp>" \
            "<tcpport>%(port)u</tcpport>" \
            "<tcplocalport>%(port)u</tcplocalport>" \
            "<tcpexternalport>0</tcpexternalport>" % \
            {"port":  media.ports[0]}
        for i, addr in enumerate(media.ips):
            body += "<tcpipaddress%u>%s</tcpipaddress%u>" % (i + 1, addr, i + 1)
        body += "</tcp>"
        body += "<codec></codec><channelmode>2</channelmode>"
        body += "</%s>\r\n\r\n" % tag
        return body

class WebcamMediaDescription(object):

    def __init__(self, sid, producer):
        self._ips = []
        self._ports = []
        self._rid = None
        self._sid = sid
        self._direction = producer and MediaStreamDirection.SENDING or \
                MediaStreamDirection.RECEIVING

    @property
    def name(self):
        return "video"

    @property
    def direction(self):
        return self._direction

    @rw_property
    def codecs():
        def fget(self):
            return [SDPCodec(4294967295, "mimic", 0)]
        def fset(self, value):
            pass
        return locals()

    @property
    def ips(self):
        return self._ips

    @property
    def ports(self):
        return self._ports

    @rw_property
    def rid():
        def fget(self):
            return self._rid
        def fset(self, value):
            self._rid = value
        return locals()

    @rw_property
    def sid():
        def fget(self):
            return self._sid
        def fset(self, value):
            self._sid = value
        return locals()

    def get_attribute(self, name):
        return False
