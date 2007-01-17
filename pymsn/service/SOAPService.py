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

import logging
logger = logging.getLogger('Service')

class BaseSOAPService(object):
    DEFAULT_PROTOCOL = "http"

    def __init__(self, url, proxy=None):
        protocol, host, self.resource = self._url_split(url)
        self.http_headers = {}
        self.request = None
        self.request_queue = []
        self.transport = gnet.protocol.ProtocolFactory(protocol, host, proxy=proxy)
        self.transport.connect("response-received", self._response_handler)
        self.transport.connect("request-sent", self._request_handler)
        self.transport.connect("error", self._error_handler)

    def _url_split(self, url):
        from urlparse import urlsplit, urlunsplit
        if "://" not in url: # fix a bug in urlsplit
            url = self.DEFAULT_PROTOCOL + "://" + url
        protocol, host, path, query, fragment = urlsplit(url)
        if path == "": path = "/"
        resource = urlunsplit(('', '', path, query, fragment))
        return protocol, host, resource

    def _response_handler(self, transport, response):
        logger.debug("<<< " + str(response))

    def _request_handler(self, transport, request):
        logger.debug(">>> " + str(request))
    
    def _error_handler(self, transport, error):
        logger.warning("Transport Error :" + str(error))

    def _send_request(self):
        """This method sends the SOAP request over the wire"""
        self.transport.request(resource = self.resource,
                headers = self.http_headers,
                data = str(self.request),
                method = 'POST')
        self.http_headers = {}
        self.soap_headers = None
        self.request = None


class SOAPService(BaseSOAPService):
    """Base class for all Windows Live Services."""
    
    def __init__(self, url, proxy=None):
        BaseSOAPService.__init__(self, url, proxy)

    def __getattr__(self, name):
        def method(*params):
            self._simple_method(name, *params)
        method.__name__ = name
        return method
    
    def _method(self, method_name, attributes, *params):
        """Used for method construction, the SOAP tree is built
        but not sent, so that the ComplexMethods can use it and add
        various things to the SOAP tree before sending it"""
        ns = self._method_namespace(method_name)
        request = SOAP.SOAPRequest(method_name, ns, **attributes)
        for param in params:
            assert(len(param) == 2 or len(param) == 3)
            if len(param) == 2:
                request.add_argument(param[0], value=param[1])
            elif len(param) == 3:
                request.add_argument(param[1], type=param[0], value=param[2])
        self.request = request
        self._soap_headers(method_name)
        self._http_headers(method_name)
        self.request_queue.append(method_name)

    def _simple_method(self, method_name, *params):
        """Methods that are auto handled"""
        self._method(method_name, {}, *params)
        self._send_request()

    def _response_handler(self, transport, response):
        BaseSOAPService._response_handler(self, transport, response)
        soap_response = SOAP.SOAPResponse(response.body)
        method = self.request_queue.pop(0)
        self._extract_response(method, soap_response)
    
    def _extract_response(self, method, soap_response):
        pass

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
        if self._soap_action(method):
            self.http_headers['SOAPAction'] = self._soap_action(method)
        self.http_headers['Content-Type'] = "text/xml; charset=utf-8"


