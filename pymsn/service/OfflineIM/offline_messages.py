# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import rsi
import oim
import scenario

import gobject

__all__ = ['OfflineMessages']

class OfflineMessages(gobject.GObject):

    def __init__(self, sso, proxies=None):
        gobject.GObject.__init__(self)

        self._rsi = rsi.RSI(sso, proxies)
        self._oim = oim.OIM(sso, proxies)

gobject.type_register(OfflineMessages)
