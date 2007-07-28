# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

from pymsn.gnet.message.HTTP import HTTPMessage
from pymsn.msnp2p.expections import ParseError


class SLPMessage(HTTPMessage):
    STD_HEADERS = [ "To", "From", "Via", "CSeq", "Call-ID", "Max-Forwards" ]

    STATUS_MESSAGE =  {
            200 : "200 OK",
            404 : "404 Not Found",
            500 : "500 Internal Error",
            603 : "603 Decline",
            606 : "Unacceptable",
            }
    
    def __init__(self, to="", frm="", branch="", cseq=1, call_id="", max_forwards=0):
        HTTPMessage.__init__(self)

        self.add_header("To", "<msnmsgr:%s>" % to)
        self.add_header("From", "<msnmsgr:%s>" % frm)
        if branch:
            self.add_header("Via", "MSNSLP/1.0/TLP ;branch=%s" % branch)
        self.add_header("CSeq", str(cseq))
        if call_id:
            self.add_header("Call-ID", call_id)
        self.add_header("Max-Forwards", str(max_forwards))

    @staticmethod
    def parse(raw_message):
        if raw_message.find("MSNSLP/1.0") < 0:
            raise ParseError("message doesn't seem to be an MSNSLP/1.0 message")
        start_line, content = raw_message.split("\r\n", 1)
        start_line = start_line.split(" ")

        if start_line[0].strip() in ("INVITE", "BYE", "ACK"):
            method = start_line[0].strip()
            slp_message = SLPRequestMessage(method)
        else:
            status = int(start_line[1].strip())
            slp_message = SLPResponseMessage(status)
        slp_message.parse(content)
        return slp_message


class SLPRequestMessage(SLPMessage):
    def __init__(self, method, *args, **kwargs):
        SLPMessage.__init_(self, *args, **kwargs)
        self.method = method
        
class SLPResponseMessage(SLPMessage):
    def __init__(self, status, *args, **kwargs):
        SLPMessage.__init_(self, *args, **kwargs)
        self.status = int(status)

