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
import papyon.util.element_tree as ElementTree
import struct

import papyon.util.guid as guid

import gobject
import base64
import random
#Farsight/GStreamer imports
import pygst
pygst.require('0.10')
import farsight, gst, gobject, sys

__all__ = ['IncomingP2PSession', 'OutgoingP2PSession','WebcamSessionRecv,WebcamSessionSend']

MAX_INT32 = 0x7fffffff
MAX_INT16 = 0x7fff

def _generate_id(max=MAX_INT32):
    """
    Returns a random ID.

        @return: a random integer between 1000 and sys.maxint
        @rtype: integer
    """
    return random.randint(1000, max)


class P2PSession(gobject.GObject):
    __gsignals__ = {
            "transfer-completed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
    }
    def __init__(self, session_manager, peer, euf_guid="", application_id=0):
        gobject.GObject.__init__(self)
        self._session_manager = session_manager
        self._peer = peer

        self._id =  _generate_id()
        self._call_id = "{%s}" % guid.generate_guid()

        self._euf_guid = euf_guid
        self._application_id = application_id

        self._cseq = 0
        self._branch = "{%s}" % guid.generate_guid()
        self._session_manager._register_session(self)

    @property
    def id(self):
        return self._id

    @property
    def call_id(self):
        return self._call_id

    @property
    def peer(self):
        return self._peer

    def _close(self):
        body = SLPSessionCloseBody()
        self._cseq = 0
        self._branch = "{%s}" % guid.generate_guid()
        message = SLPRequestMessage(SLPRequestMethod.BYE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_p2p_data(message)
        self._session_manager._unregister_session(self)

    def _send_p2p_data(self, data_or_file):
        if isinstance(data_or_file, SLPMessage):
            session_id = 0
            data = str(data_or_file)
            total_size = len(data)
        else:
            session_id = self._id
            data = data_or_file
            total_size = None

        blob = MessageBlob(self._application_id,
                data, total_size, session_id)
        self._session_manager._transport_manager.send(self.peer, blob)

    def _on_blob_sent(self, blob):
        if blob.session_id == 0:
            # FIXME: handle the signaling correctly
            return

        if blob.total_size == 4 and \
                blob.data.read() == ('\x00' * 4):
            self._on_data_preparation_blob_sent(blob)
        else:
            self._on_data_blob_sent(blob)

    def _on_blob_received(self, blob):
        if blob.session_id == 0:
            # FIXME: handle the signaling correctly
            return

        if blob.total_size == 4 and \
                blob.data.read() == ('\x00' * 4):
            self._on_data_preparation_blob_received(blob)
        else:
            self._on_data_blob_received(blob)
            self._close()

    def _on_data_preparation_blob_received(self, blob):
        pass

    def _on_data_preparation_blob_sent(self, blob):
        pass

    def _on_data_blob_sent(self, blob):
        blob.data.seek(0, 0)
        self.emit("transfer-completed", blob.data)

    def _on_data_blob_received(self, blob):
        blob.data.seek(0, 0)
        self.emit("transfer-completed", blob.data)

gobject.type_register(P2PSession)


class IncomingP2PSession(P2PSession):
    def __init__(self, session_manager, peer, id, message):
        P2PSession.__init__(self, session_manager, peer,
                message.body.euf_guid, message.body.application_id)
        self._id =  id
        self._call_id = message.call_id

        self._cseq = message.cseq
        self._branch = message.branch
        try:
            self._context = message.body.context.strip('\x00')
        except AttributeError:
            raise SLPError("Incoming INVITE without context")

    def accept(self, data_file):
        #Made an edit here, removing the file transfer code 
        #gobject.idle_add(self._start_transfer, data_file)
        self._respond(200)
    
    def reject(self):
        self._respond(603)

    def _respond(self, status_code):
        body = SLPSessionRequestBody(session_id=self._id,capabilities_flags=None,s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)

    def _start_transfer(self, data_file):
        self._respond(200)
        self._send_p2p_data("\x00" * 4)
        self._send_p2p_data(data_file)
        return False

class OutgoingP2PSession(P2PSession): 
    def __init__(self, session_manager, peer, context, euf_guid, application_id):
        P2PSession.__init__(self, session_manager, peer, euf_guid, application_id)
        gobject.idle_add(self._invite, str(context))

    def _invite(self, context):
        self._session_manager._register_session(self)
        body = SLPSessionRequestBody(self._euf_guid, self._application_id,
                context, self._id)

        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)

        message.body = body
        self._send_p2p_data(message)
        return False
 
class WebcamSession(P2PSession): #Based off P2PSession, rework to base off OutgoingSession? 
    
    def __init__(self, producer, session_manager, peer, \
                     euf_guid, application_id, \
                     session_id = None, message = None):
        P2PSession.__init__(self, session_manager, peer, \
                                euf_guid, application_id)
        
        self._producer = producer
        if session_id is None:
            self._id =  _generate_id()
        else:
            self._id = session_id

        if message is not None:
            self._call_id = message.call_id
            self._cseq = message.cseq
            self._branch = message.branch

        self._pipeline = None
        self._sent_syn = False
        self._session_manager._register_session(self)

  
    def invite(self):
        context = "{B8BE70DE-E2CA-4400-AE03-88FF85B9F4E8}"
        body = SLPSessionRequestBody(EufGuid.MEDIA_SESSION,ApplicationID.WEBCAM,
                context.decode('ascii').encode('utf-16_le'), self._id)
        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body

        self._call_id = message.call_id
        self._cseq = message.cseq
        self._branch = message.branch
        self._send_p2p_data(message)
        
    def _respond(self, status_code):
        body = SLPSessionRequestBody(session_id=self._id,capabilities_flags=None,s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)


    def accept(self):
        temp_application_id = self._application_id
        self._application_id = 0
        self._respond(200)
        self.send_transreq()
        self._application_id = temp_application_id

    def _send_req(self):
        body = SLPSessionRequestBody(session_id=self._id, \
                                         capabilities_flags=None, \
                                         s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)
        
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
        if blob.session_id == 0:
            # FIXME: handle the signaling correctly
            # Determine if it actually is a transreq or not
            # send 603
            return
        data = blob.data.read()
        if not self._sent_syn:
            self.send_binary_syn() #Send 603 first ?
        if '\x00s\x00y\x00n\x00\x00\x00' in data:
            self.send_binary_ack()
        elif '\x00a\x00c\x00k\x00\x00\x00' in data:
            if self._producer:
                self._setup_conference(farsight.DIRECTION_SEND)
            pass
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
        session_id = self._fssession.get_property("session-id")
        if self._producer:
            s = "<producer>"
        else:
            s = "<viewer>"
        s += "<version>2.0</version><rid>%s</rid><session>%u</session><ctypes>0</ctypes><cpu>2010</cpu>" % \
            (self._local_candidates[0].foundation,
             session_id)
        
        s += "<tcp>"
        s += "<tcpport>%(port)u</tcpport>\t\t\t\t\t\t\t\t  <tcplocalport>%(port)u</tcplocalport>\t\t\t\t\t\t\t\t  <tcpexternalport>%(port)u</tcpexternalport>" \
            % { "port" : self._local_candidates[0].port }
        for i, candidate in enumerate(self._local_candidates):
            s += "<tcpipaddress%u>%s</tcpipaddress%u>" % (i + 1, candidate.ip, i + 1)
        s += "</tcp>"
        s += "<codec></codec><channelmode>2</channelmode>"
        
        if self._producer:
            s += "</producer>"
        else:
            s += "</viewer>"
        s += "\r\n\r\n"
        message_bytes = s.encode("utf-16-le") + "\x00\x00"
        id = (_generate_id() << 8) | 0x80
        header = struct.pack("<LHL", id, 8, len(message_bytes))
        self._send_p2p_data(header+message_bytes)
        if self._producer is False:
            self._stream.set_remote_candidates (self._remote_candidates)
            self._pipeline.set_state(gst.STATE_PLAYING)
            self._remote_candidates = None
            
        
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
        session_id = int(tree.find("session").text)

        candidates = []
        for ip in ips:
            for port in ports:
                candidate = farsight.Candidate()
                candidate.ip = ip 
                candidate.port = port
                candidate.ttl = 1
                candidate.foundation = rid
                candidates.append(candidate)

        # Signalling is done, now pass it off to the handler to control it further
        print "Received xml %s" % message
        if self._producer:
            self.send_binary_viewer_data()
            self._stream.set_remote_candidates (candidates)
            self._pipeline.set_state(gst.STATE_PLAYING)
        else:
            self._remote_candidates = candidates
            self._setup_conference(farsight.DIRECTION_RECV, session_id)



    def _on_bus_message(self, bus, msg):
        if msg.type == gst.MESSAGE_ELEMENT:
            s = msg.structure
            if s.has_name("farsight-new-local-candidate"):
                self._local_candidates.append(s["candidate"])
            if s.has_name("farsight-local-candidates-prepared"):
                self._send_xml()

            print "Received message on bus : %s" % s

    def _src_pad_added(self, stream, pad, codec):
        print "SOURCE PAD ADDED"
        self._videosink = self.make_video_sink()
        self._pipeline.add (self._videosink)
        self._videosink.set_state(gst.STATE_PLAYING)
        pad.link(self._videosink.get_pad("sink"))

    def _setup_conference(self, direction, session_id=0):
        self._local_candidates = []
        self._pipeline = gst.Pipeline()
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message)

        self._conference = gst.element_factory_make ("fsmsnconference")
       
        # For fututre work, when implementing the msn video conferencing
        # the variables below should be renamed to be type specific,
        # i.e. self._session_video etc
        self._pipeline.add (self._conference)
        self._fssession = \
            self._conference.new_session (farsight.MEDIA_TYPE_VIDEO)
        if session_id != 0:
            self._fssession.set_property("session-id", session_id)

        participant = self._conference.new_participant (self._peer.account)
        if direction == farsight.DIRECTION_SEND: 
            self._stream = \
                self._fssession.new_stream (participant, \
                                                farsight.DIRECTION_SEND, \
                                                None)
            self._videosrc = self.make_video_source()
            self._pipeline.add (self._videosrc)
            self._videosrc.get_pad("src"). \
                link(self._fssession.get_property ("sink-pad"))
            self._videosrc.set_state(gst.STATE_PLAYING)
        elif direction == farsight.DIRECTION_RECV:
            self._stream = \
                self._fssession.new_stream (participant, \
                                                   farsight.DIRECTION_RECV, \
                                                   None)
            self._stream.connect("src-pad-added", self._src_pad_added)
        else:
            print "Error not send or receive direction in conference setup"
            return

    def make_video_source(self, name="videotestsrc"):
        "Make a bin with a video source in it, defaulting to first webcamera "
        bin = gst.Bin("videosrc")
        src = gst.element_factory_make(name, name)
        bin.add(src)
        colorspace = gst.element_factory_make("ffmpegcolorspace")
        bin.add(colorspace)
        videoscale = gst.element_factory_make("videoscale")
        bin.add(videoscale)
        src.link(colorspace)
        colorspace.link(videoscale)
        bin.add_pad(gst.GhostPad("src", videoscale.get_pad("src")))
        return bin
        
    def make_video_sink(self, async=False):
        "Make a bin with a video sink in it, that will be displayed on xid."
        bin = gst.Bin("videosink")
        sink = gst.element_factory_make("ximagesink", "imagesink")
        sink.set_property("sync", async)
        sink.set_property("async", async)
        bin.add(sink)
        colorspace = gst.element_factory_make("ffmpegcolorspace")
        bin.add(colorspace)
        videoscale = gst.element_factory_make("videoscale")
        bin.add(videoscale)
        videoscale.link(colorspace)
        colorspace.link(sink)
        bin.add_pad(gst.GhostPad("sink", videoscale.get_pad("sink")))
        #sink.set_data("xid", xid) #Future work - proper gui place for imagesink ?
        return bin
    
class WebcamSessionRecv(P2PSession):  
    
    def __init__(self, session_manager,peer,euf_guid, application_id,session_id,message,):
        P2PSession.__init__(self, session_manager, peer, euf_guid, application_id)
        
        self._id =  session_id
        self.message = message
        self._pipeline = None
        self._call_id = self.message.call_id
        self._state = 0
        self._cseq = self.message.cseq
        self._branch = self.message.branch
        
        self._local_ip = self._session_manager._client._webcam_handler.local_ip
        self._local_port = self._session_manager._client._webcam_handler.local_port
    
    def _send_req(self):
        body = SLPSessionRequestBody(session_id=self._id,capabilities_flags=None,s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)
        
    def _respond(self, status_code):
        body = SLPSessionRequestBody(session_id=self._id,capabilities_flags=None,s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)
    
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
        
    def _on_blob_received(self, blob):
        if blob.session_id == 0:
            # FIXME: handle the signaling correctly
            return
        data = blob.data.read()
        if '\x00s\x00y\x00n\x00\x00\x00' in data:
            self.send_binary_syn()
            self._state +=1
        elif '\x00a\x00c\x00k\x00\x00\x00' in data:
            self.send_binary_ack()
            self._state +=1
        elif (self._state == 2):
            self._handle_xml(blob)
        
    def send_binary_syn(self):
        syn='\x80\x11\x11\x01\x08\x00\x08\x00\x00\x00s\x00y\x00n\x00\x00\x00'
        footer='\x00\x00\x00\x04'
        self._send_p2p_data(syn)
        
    def send_binary_ack(self):
        ack='\x80\xea\x00\x00\x08\x00\x08\x00\x00\x00a\x00c\x00k\x00\x00\x00'
        footer='\x00\x00\x00\x04'
        self._send_p2p_data(ack)
        
    def _handle_xml(self,blob):
    
        local_ip = self._local_ip
        local_port = self._local_port
        self._state = 0
        blob.data.seek(10, 0)
        data = blob.data.read()
        datastr = str(data).replace("\000","")
        message = unicode(data, "utf-16-le").rstrip("\x00")
        tree = ElementTree.fromstring(datastr)
        self.remote_ips = []
        self.port = -1
        for node in tree.findall("tcp/*"):
            if node.tag == "tcpport":
                self.port = int(node.text)
            elif node.tag.startswith("tcpipaddress"):
                self.remote_ips.append(node.text)
        self._remote_rid = int(tree.find("rid").text)
        self._vid_session = int(tree.find("session").text)
        self._local_rid = random.randint(100, 200)
        if self._local_rid == self._remote_rid:
            self._local_rid += 2

        s = "<viewer>"
        s += "<version>2.0</version><rid>%u</rid><session>%u</session><ctypes>0</ctypes><cpu>2010</cpu>" % \
            (self._local_rid,self._vid_session)
        
        s += "<tcp>"
        s += "<tcpport>%(port)u</tcpport>\t\t\t\t\t\t\t\t  <tcplocalport>%(port)u</tcplocalport>\t\t\t\t\t\t\t\t  <tcpexternalport>%(port)u</tcpexternalport>" \
            % { "port" : local_port }
        for i, ip in enumerate(local_ip):
            s += "<tcpipaddress%u>%s</tcpipaddress%u>" % (i + 1, ip, i + 1)
        s += "</tcp>"
        s += "<codec></codec><channelmode>2</channelmode>"
        s += "</viewer>\r\n\r\n"
        message_bytes = s.encode("utf-16-le") + "\x00\x00"
        id = (_generate_id() << 8) | 0x80
        header = struct.pack("<LHL", id, 8, len(message_bytes))
        self._send_p2p_data(header+message_bytes)
        self._session_manager._client._webcam_handler.setup_multimedia(self,farsight.DIRECTION_RECV )
        
