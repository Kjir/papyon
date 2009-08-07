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

__all__ = ['WebcamSession']

class WebcamSession(P2PSession, EventsDispatcher):

    def __init__(self, producer, session_manager, peer,
            euf_guid,  message = None):
        P2PSession.__init__(self, session_manager, peer, euf_guid,
                ApplicationID.WEBCAM, message)
        EventsDispatcher.__init__(self)

        self._producer = producer
        self._sent_syn = False
        self._local_candidates = None
        self._remote_candidates = None
        self._session_id = 0
        self._xml_needed = False

    @rw_property
    def local_candidates():
        def fget(self):
            return self._local_candidates
        def fset(self, candidates):
            self._local_candidates = candidates
            if self._xml_needed and self._session_id != 0:
                self._send_xml()
                self._xml_needed = False
        return locals()

    @rw_property
    def session_id():
        def fget(self):
            return self._session_id
        def fset(self, session_id):
            self._session_id = session_id
            if self._xml_needed and self._local_candidates != 0:
                self._send_xml()
                self._xml_needed = False
        return locals()

    @property
    def remote_candidates(self):
        return self._remote_candidates
  
    @property
    def codecs(self):
        return [Codec.ML20]
  
    def invite(self):
        context = "{B8BE70DE-E2CA-4400-AE03-88FF85B9F4E8}"
        context = context.decode('ascii').encode('utf-16_le')
        self._invite(context)

    def accept(self):
        temp_application_id = self._application_id
        self._application_id = 0
        self._respond(200)
        self.send_transreq()
        self._application_id = temp_application_id

    def reject(self):
        self._respond(603)

    def send_transreq(self):
        self._cseq=0
        body = SLPTransferRequestBody(self._euf_guid, self._application_id,None,
                                     None)
        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._application_id=0
        self._send_p2p_data(message)
        self._application_id=4
        self.send_binary_syn()

    def _on_blob_received(self, blob):
        data = blob.data.read()

        if blob.session_id == 0:
            message = SLPMessage.build(data)
            if isinstance(message, SLPResponseMessage):
                if message.status is 200:
                    self._dispatch("on_webcam_accepted")
                elif message.status is 603:
                    self._dispatch("on_webcam_rejected")

            # FIXME: handle the signaling correctly
            # Determine if it actually is a transreq or not
            # send 603
            return

        if not self._sent_syn:
            self.send_binary_syn() #Send 603 first ?
        if '\x00s\x00y\x00n\x00\x00\x00' in data:
            self.send_binary_ack()
        elif '\x00a\x00c\x00k\x00\x00\x00' in data:
            if self._producer:
                if self._local_candidates is not None:
                    self._send_xml()
                else:
                    self._xml_needed = True
        elif ('\x00<\x00p\x00r\x00o\x00d\x00u\x00c\x00e\x00r\x00>\x00' in data) \
                or ('\x00<\x00v\x00i\x00e\x00w\x00e\x00r\x00>\x00' in data):
            self._handle_xml(blob)

    def send_binary_syn(self):
        syn='\x80\x11\x11\x01\x08\x00\x08\x00\x00\x00s\x00y\x00n\x00\x00\x00'
        footer='\x00\x00\x00\x04'
        self._send_p2p_data(syn)
        self._sent_syn = True
        
    def send_binary_ack(self):
        ack='\x80\xea\x00\x00\x08\x00\x08\x00\x00\x00a\x00c\x00k\x00\x00\x00'
        footer='\x00\x00\x00\x04'
        self._send_p2p_data(ack)
        
    def send_binary_viewer_data(self):
        data = '\x80\xec\xc7\x03\x08\x00&\x00\x00\x00r\x00e\x00c\x00e\x00i\x00v\x00e\x00d\x00V\x00i\x00e\x00w\x00e\x00r\x00D\x00a\x00t\x00a\x00\x00\x00'
        footer='\x00\x00\x00\x04'
        self._send_p2p_data(data)

    def _send_xml(self):
        if self._producer:
            s = "<producer>"
        else:
            s = "<viewer>"

        s += "<version>2.0</version><rid>%s</rid><session>%u</session><ctypes>0</ctypes><cpu>2010</cpu>" % \
            (self._local_candidates[0][2],
             self._session_id)
        
        s += "<tcp>"
        s += "<tcpport>%(port)u</tcpport>\t\t\t\t\t\t\t\t  <tcplocalport>%(port)u</tcplocalport>\t\t\t\t\t\t\t\t  <tcpexternalport>%(port)u</tcpexternalport>" \
            % { "port" : self._local_candidates[0][1] }
        for i, candidate in enumerate(self._local_candidates):
            s += "<tcpipaddress%u>%s</tcpipaddress%u>" % (i + 1, candidate[0], i + 1)
        s += "</tcp>"
        s += "<codec></codec><channelmode>2</channelmode>"
        
        if self._producer:
            s += "</producer>"
        else:
            s += "</viewer>"
        s += "\r\n\r\n"
        message_bytes = s.encode("utf-16-le") + "\x00\x00"
        id = (self._generate_id() << 8) | 0x80
        header = struct.pack("<LHL", id, 8, len(message_bytes))
        self._send_p2p_data(header+message_bytes)

    def _handle_xml(self,blob):
        blob.data.seek(10, 0)
        data = blob.data.read()
        datastr = str(data).replace("\000","")
        message = unicode(data, "utf-16-le").rstrip("\x00")
        tree = ElementTree.fromstring(datastr)
        ips = []
        ports = []
        for node in tree.findall("tcp/*"):
            if node.tag == "tcpport":
                ports.append(int(node.text))
            elif node.tag.startswith("tcpipaddress"):
                ips.append(node.text)
        rid = tree.find("rid").text
        self._session_id = int(tree.find("session").text)

        self._remote_candidates = []
        for ip in ips:
            for port in ports:
                candidate = (ip, port, rid)
                self._remote_candidates.append(candidate)

        # Signalling is done, now pass it off to the handler to control it further
        print "Received xml %s" % message
        self._dispatch("on_webcam_viewer_data_received", self._session_id, rid, self._remote_candidates)
        if self._producer:
            self.send_binary_viewer_data()
        elif self._local_candidates is not None:
            self._send_xml()
        else:
            self._xml_needed = True
