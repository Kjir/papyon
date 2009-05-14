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

class CodecRtpmap(unittest.TestCase):
    codecs = [ ((8, "PCMA", 8000), "8 PCMA/8000"),
               ((0, "PCMU", 8000), "0 PCMU/8000")]

    def testBuilding(self):
        for args, string in self.codecs:
            codec = Codec(*args)
            self.assertEqual(codec.build_rtpmap(), string)

    def testParsing(self):
        for args, string in self.codecs:
            codec = Codec()
            codec.parse_rtpmap(string)
            self.assertEqual(codec.payload, args[0])
            self.assertEqual(codec.encoding, args[1])
            self.assertEqual(codec.bitrate, args[2])


if __name__ == "__main__":
    sys.path.insert(0, "")
    from papyon.sip.sdp import *
    unittest.main()
