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

import sys
import unittest

definitions19 = [
((1, 1, "UDP", 2013266431, "192.168.1.107", 54751, "host", None, None),
"1 1 UDP 2013266431 192.168.1.107 54751 typ host"),
((3, 1, "UDP", 1677721855, "70.25.46.249", 54751, "srflx", "192.168.1.107", 54751),
"3 1 UDP 1677721855 70.25.46.249 54751 typ srflx raddr 192.168.1.107 rport 54751"),
((4, 1, "UDP", 1006633215, "64.4.35.48", 30797, "relay", "192.168.1.107", 54751),
"4 1 UDP 1006633215 64.4.35.48 30797 typ relay raddr 192.168.1.107 rport 54751"),
((1, 2, "UDP", 2013266430, "192.168.1.107", 49259, "host", None, None),
"1 2 UDP 2013266430 192.168.1.107 49259 typ host"),
((3, 2, "UDP", 1677721854, "70.25.46.249", 49259, "srflx", "192.168.1.107", 49259),
"3 2 UDP 1677721854 70.25.46.249 49259 typ srflx raddr 192.168.1.107 rport 49259"),
((4, 2, "UDP", 1006633214, "64.4.35.48", 45694, "relay", "192.168.1.107", 49259),
"4 2 UDP 1006633214 64.4.35.48 45694 typ relay raddr 192.168.1.107 rport 49259")]

definitions6 = [
(("gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg=", 1,
  "AT6jQtrWTfVi7S1Ko4pBxA==", "UDP", 0.830, "192.168.1.107", 54183),
"gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg= 1 AT6jQtrWTfVi7S1Ko4pBxA== UDP 0.830 192.168.1.107 54183"),
(("wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM=", 1,
  "wWRgVlW33BSPYwEZrsFwFg==", "UDP", 0.550, "70.25.46.249", 54183),
"wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM= 1 wWRgVlW33BSPYwEZrsFwFg== UDP 0.550 70.25.46.249 54183"),
(("AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY=", 1,
  "iVxzBYjmxFxOHI4e3ZMq6A==", "UDP", 0.450, "64.4.34.204", 32594),
"AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY= 1 iVxzBYjmxFxOHI4e3ZMq6A== UDP 0.450 64.4.34.204 32594"),
(("gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg=", 2,
  "AT6jQtrWTfVi7S1Ko4pBxA==", "UDP", 0.830, "192.168.1.107", 43701),
"gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg= 2 AT6jQtrWTfVi7S1Ko4pBxA== UDP 0.830 192.168.1.107 43701"),
(("wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM=", 2,
  "wWRgVlW33BSPYwEZrsFwFg==", "UDP", 0.550, "70.25.46.249", 43701),
"wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM= 2 wWRgVlW33BSPYwEZrsFwFg== UDP 0.550 70.25.46.249 43701"),
(("AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY=", 2,
  "iVxzBYjmxFxOHI4e3ZMq6A==", "UDP", 0.450, "64.4.34.204", 56585),
"AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY= 2 iVxzBYjmxFxOHI4e3ZMq6A== UDP 0.450 64.4.34.204 56585")]


class CandidateTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def assertCandidate19(self, candidate, args):
        self.assertEqual(candidate.foundation, args[0])
        self.assertEqual(candidate.component_id, args[1])
        self.assertEqual(candidate.transport, args[2])
        self.assertEqual(candidate.priority, args[3])
        self.assertEqual(candidate.ip, args[4])
        self.assertEqual(candidate.port, args[5])
        self.assertEqual(candidate.type, args[6])
        self.assertEqual(candidate.base_ip, args[7])
        self.assertEqual(candidate.base_port, args[8])

    def assertCandidate6(self, candidate, args):
        self.assertEqual(candidate.username, args[0])
        self.assertEqual(candidate.component_id, args[1])
        self.assertEqual(candidate.password, args[2])
        self.assertEqual(candidate.transport, args[3])
        self.assertEqual(candidate.priority, args[4])
        self.assertEqual(candidate.ip, args[5])
        self.assertEqual(candidate.port, args[6])

    def createCandidate19(self, args):
        return Candidate(draft=19, 
                         foundation=args[0],
                         component_id=args[1],
                         transport=args[2],
                         priority=args[3],
                         ip=args[4],
                         port=args[5],
                         type=args[6],
                         base_ip=args[7],
                         base_port=args[8])

    def createCandidate6(self, args):
        return Candidate(draft=6, 
                         username=args[0],
                         component_id=args[1],
                         password=args[2],
                         transport=args[3],
                         priority=args[4],
                         ip=args[5],
                         port=args[6])

    def testParse19(self):
        for args, line in definitions19:
            candidate = Candidate(draft=19)
            candidate.parse(line)
            self.assertCandidate19(candidate, args)

    def testBuildLocal19(self):
        for args, line in definitions19:
            candidate = self.createCandidate19(args)
            print candidate.build_local()

    def testBuildParse19(self):
        for args, line in definitions19:
            candidate = self.createCandidate19(args)
            line = candidate.build_local()
            candidate = Candidate(draft=19)
            candidate.parse(line)
            self.assertCandidate19(candidate, args)

    def testParse6(self):
        for args, line in definitions6:
            candidate = Candidate(draft=6)
            candidate.parse(line)
            self.assertCandidate6(candidate, args)

    def testBuildLocal6(self):
        for args, line in definitions6:
            candidate = self.createCandidate6(args)
            self.assertEqual(candidate.build_local(), line)

    def testBuildParse19(self):
        for args, line in definitions6:
            candidate = self.createCandidate6(args)
            line = candidate.build_local()
            candidate = Candidate(draft=6)
            candidate.parse(line)
            self.assertCandidate6(candidate, args)


if __name__ == "__main__":
    sys.path.insert(0, "")
    from papyon.sip.ice import *
    unittest.main()
