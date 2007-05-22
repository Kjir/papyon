# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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

import pymsn.gnet.protocol
import pymsn.gnet.message.SOAP as SOAP

import logging
logger = logging.getLogger('Service')

class SOAPUtils(object):
    def __init__(self, ns_shorthands):
        self._ns_shorthands = ns_shorthands

    def find_ex(self, xml_node, path):
        return SOAPUtils.find(xml_node, path, self._ns_shorthands)

    @staticmethod
    def find(xml_node, path, ns_shorthands):
        for sh, ns in ns_shorthands.iteritems():
            path = path.replace("/%s:" % sh, "/{%s}" % ns)
        return xml_node.find(path)

    @staticmethod
    def bool_type(s):
        if s.lower() in ("false", "no", "f", "n", "0", ""):
            return False
        return True

    @staticmethod
    def bool_to_string(b):
        if b: return "true"
        return "false"

    @staticmethod
    def int_type(s):
        try:
            return int(s)
        except:
            return 0

class SOAPFault(Exception):

    SOAP_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"
    NS_SHORTHANDS = { "soap": SOAP_ENVELOPE }

    def __init__(self, xml_node):
        self._soap_utils = SOAPUtils(SOAPFault.NS_SHORTHANDS)
        fault = self._soap_utils.find_ex(xml_node, "./soap:Fault")
        self.code = self._soap_utils.find_ex(fault, "./faultcode").text
        self.string = self._soap_utils.find_ex(fault, "./faultstring").text
        #self.actor = self._soap_utils.find_ex(fault, "./faultactor").text

    def __str__(self):
        return "SOAPFault : " + self.string

class BaseSOAPService(object):
    DEFAULT_PROTOCOL = "http"

    def __init__(self, url, proxy=None):
        protocol, host, self.resource = self._url_split(url)
        self.http_headers = {}
        self.request = None
        self.request_queue = []
        self.transport = pymsn.gnet.protocol.ProtocolFactory(protocol, host, proxy=proxy)
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
        soap_response = SOAP.SOAPResponse(response.body)
        #logger.debug("<<< SOAP Response: " + soap_response.body[0].tag)

    def _request_handler(self, transport, request):
        logger.debug(">>> " + str(request))
        soap_request = SOAP.SOAPResponse(request.body)
        #logger.debug(">>> SOAP Request: " + soap_request.body[0].tag)

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
        self._response_extractor = {}

    def __getattr__(self, name):
        def method(callback, *params):
            self._simple_method(name, callback, *params)
        method.__name__ = name
        return method

    def _method(self, method_name, callback, callback_args, attributes, *params):
        """Used for method construction, the SOAP tree is built
        but not sent, so that the ComplexMethods can use it and add
        various things to the SOAP tree before sending it.

            @param method_name: the SOAP method name
            @type method_name: string

            @param callback: the callback to use when the response is received
            @type callback: callable(callback_args, response)

            @param callback_args: additional arguments to be passed to the callback
            @type callback_args: tuple(callback)

            @param attributes: the attributes to be attached to the method call
            @type attributes: dict

            @param params: tuples containing the attribute name and the
                attribute value
            @type params: tuple(name, value) or tuple(type, name, value)

            @note: this method does not actually send the request and
            L{_send_request} must be called"""
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
        self.request_queue.append((method_name, callback, callback_args))

    def _simple_method(self, method_name, callback, callback_args, *params):
        """Methods that are auto handled.

            @param method_name: the SOAP method name
            @type method_name: string

            @param callback: the callback to use when the response is received
            @type callback: callable(response)

            @param callback_args: additional arguments to be passed to the callback
            @type callback_args: tuple(callback)

            @param params: tuples containing the attribute name and the
                attribute value
            @type params: tuple(name, value) or tuple(type, name, value)"""
        self._method(method_name, callback, callback_args, {}, *params)
        self._send_request()

    def _response_handler(self, transport, response):
        BaseSOAPService._response_handler(self, transport, response)
        soap_response = SOAP.SOAPResponse(response.body)
        method, callback, callback_args = self.request_queue.pop(0)
        if callback is not None:
            result = self._extract_response(method, soap_response)
            arguments = tuple(callback_args)
            if result is not None: arguments += tuple(result)
            callback(*arguments)

    def _extract_response(self, method, soap_response):
        if method in self._response_extractor:
            result = [soap_response]
            values = self._response_extractor[method]
            for value in values:
                result.append(soap_response.find(value))
            return tuple(result)
        return (soap_response,)

    def _soap_action(self, method):
        """return the SOAPAction header value to be used
        for the given method.

            @param method: the method name
            @type method: string"""
        raise NotImplementedError

    def _method_namespace(self, method):
        """return the namespace of the given method.

            @param method: the method name
            @type method: string"""
        raise NotImplementedError

    def _soap_headers(self, method):
        """Add the needed headers for the current method"""
        pass

    def _http_headers(self, method):
        """Sets the needed http headers for the current method"""
        if self._soap_action(method):
            self.http_headers['SOAPAction'] = self._soap_action(method)
        self.http_headers['Content-Type'] = "text/xml; charset=utf-8"
        self.http_headers['Cache-Control'] ="no-cache"
        self.http_headers['Accept'] = "text/*"
        # fix : (to be removed later)
        self.http_headers["Proxy-Connection"] = "Keep-Alive"
        self.http_headers["Connection"] = "Keep-Alive"


class SOAPServiceRequest(object):
    def __init__(callback, callback_args):
        pass

