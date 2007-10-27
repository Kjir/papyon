# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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

"""GNet dns resolver"""

import socket
import threading

import gobject

__all__ = ['HostnameResolver']

class HostnameResolver(object):

    def query(self, host, port, callback, errback=None):
        worker = threading.Thread(target=self._do_query,
                args=(host, port, callback, errback))
        worker.run()


    def _do_query(self, host, port, callback, errback):
        result = socket.getaddrinfo(host, port)
        gobject.idle_add(self._emit_response, callback, result)

    def _emit_response(self, callback, result):
        callback[0](result, *callback[1:])
        return False


if __name__ == "__main__":
    mainloop = gobject.MainLoop(is_running=True)
    def print_throbber():
        print "*"
        return True

    def hostname_resolved(result):
        print result
        mainloop.quit()

    def resolve_hostname(resolver, host, port):
        print "Resolving"
        resolver.query(host, port, (hostname_resolved,))
        return False

    resolver = HostnameResolver()
    
    gobject.timeout_add(10, print_throbber)
    #gobject.timeout_add(100, resolve_hostname, resolver, 'www.google.com', 80)
    gobject.timeout_add(100, resolve_hostname, resolver, '209.85.129.104', 80)
    
    mainloop.run()

