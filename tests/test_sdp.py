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

import unittest
import sys

definitions = [ ((8, "PCMA", 8000, None), "8 PCMA/8000", ""),
                ((0, "PCMU", 8000, None), "0 PCMU/8000", ""),
                ((101, "telephone-event", 8000, "0-16"), 
                  "101 telephone-event/8000", "101 0-16")]

attributes = { "rtcp" : [42],
               "rtpmap" : ["8 PCMA/8000",
                           "0 PCMU/8000",
                           "101 telephone-event/8000"],
               "fmtp" : ["101 0-16"] }

class CodecTestCase(unittest.TestCase):

    def testBuilding(self):
        for args, rtpmap, fmtp in definitions:
            codec = Codec(*args)
            self.assertEqual(codec.build_rtpmap(), rtpmap)

    def testParsing(self):
        for args, rtpmap, fmtp in definitions:
            codec = Codec()
            codec.parse_rtpmap(rtpmap)
            self.assertEqual(codec.payload, args[0])
            self.assertEqual(codec.encoding, args[1])
            self.assertEqual(codec.bitrate, args[2])

class MediaTestCase(unittest.TestCase):

    def setUp(self):
        self.media = Media("")
        self.codecs = []
        for args, rtpmap, fmtp in definitions:
            self.codecs.append(Codec(*args))

    def testRtcpAssigned(self):
        self.media.rtcp = 42
        self.assertEqual(self.media.rtcp, 42)

    def testRtcpAssignedTwice(self):
        self.media.rtcp = 10
        self.media.rtcp = 11
        self.assertEqual(self.media.rtcp, 11)

    def testAttributeGetter(self):
        self.media.set_attribute("attr", "value")
        self.assertEqual(self.media.get_attribute("attr"), "value")

    def testAttributesGetter(self):
        self.media.add_attribute("list", 1)
        self.media.add_attribute("list", 2)
        self.assertEqual(self.media.get_attributes("list"), [1, 2])

    def testUnexistingAttribute(self):
        self.assertEqual(self.media.get_attribute("foo"), None)

    def testSetCodecs(self):
        self.media.codecs = self.codecs
        self.assertEqual(self.media.get_attributes("rtpmap"),
            attributes["rtpmap"])
        self.assertEqual(self.media.get_attributes("fmtp"),
            attributes["fmtp"])

    def testParseAttributes(self):
        for key, values in attributes.iteritems():
            for value in values:
                self.media.parse_attribute(key, value)
        self.assertEqual(self.media.rtcp, 42)
        for i in range(0, len(self.codecs)):
            self.assertEqual(self.media.codecs[i], self.codecs[i])

if __name__ == "__main__":
    sys.path.insert(0, "")
    from papyon.sip.sdp import *
    
    unittest.main()
