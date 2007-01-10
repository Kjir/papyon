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

import gnet.protocol
import gnet.message.SOAP as SOAP

class SOAPService(object):
    """Base class for all Windows Live Services."""

    def __init__(self, url):
        self.url = url
        self.http_headers = {}
        self.request = None

    def __getattr__(self, name):
        def method(*params):
            self._simple_method(name, *params)
        return method
    
    def _method(self, method_name, attributes, *params):
        ns = self._method_namespace(method_name)
        request = SOAP.SOAPRequest(method_name, ns, **attributes)
        for tag, value in params:
            request.add_argument(tag, value=value)
        self.request = request
        self._soap_headers(method_name)
        self._http_headers(method_name)

    def _simple_method(self, method_name, *params):
        """Methods that are auto handled"""
        self._method(method_name, {}, *params)
        self._send_request()
    
    def _send_request(self):
        """This method sends the SOAP request over the wire"""
        #FIXME: really send instead of printing
        from xml.dom import minidom
        print minidom.parseString(str(self.request)).toprettyxml("  ")

        self.http_headers = {}
        self.soap_headers = None
        self.request = None

    def _soap_action(self, method):
        """return the SOAPAction header value to be used
        for the given method.
            
            @param method: the method name
            @type method: string"""
        raise NotImplementedException

    def _method_namespace(self, method):
        """return the namespace of the given method.
            
            @param method: the method name
            @type method: string"""
        raise NotImplementedException

    def _soap_headers(self, method):
        """Add the needed headers for the current method"""
        pass

    def _http_headers(self, method):
        """Sets the needed http headers for the current method"""
        if self._soap_action(method) != "":
            self.http_headers['SOAPAction'] = self._soap_action(method)


