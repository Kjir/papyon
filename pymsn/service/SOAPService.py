# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import description
from SOAPUtils import *

import pymsn.gnet.protocol
import pymsn.util.ElementTree as ElementTree
import pymsn.util.StringIO as StringIO
import re
import logging

__all__ = ['SOAPService', 'SOAPResponse']

logger = logging.getLogger('Service')

def url_split(url, default_scheme='http'):
    from urlparse import urlsplit, urlunsplit
    if "://" not in url: # fix a bug in urlsplit
        url = default_scheme + "://" + url
    protocol, host, path, query, fragment = urlsplit(url)
    if path == "": path = "/"
    try:
        host, port = host.rsplit(":", 1)
        port = int(port)
    except:
        port = None
    resource = urlunsplit(('', '', path, query, fragment))
    return protocol, host, port, resource

def compress_xml(xml_string):
    space_regex = [(re.compile('>\s+<'), '><'),
        (re.compile('>\s+'), '>'),
        (re.compile('\s+<'), '<')]

    for regex, replacement in space_regex:
        xml_string = regex.sub(replacement, xml_string)
    return xml_string

soap_template = """<?xml version='1.0' encoding='utf-8'?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        %s
    </soap:Header>
    <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        %s
    </soap:Body>
</soap:Envelope>"""

class _SOAPElement(object):
    def __init__(self, element, ns_shorthands):
        self.element = element
        self.ns_shorthands = ns_shorthands.copy()

    def __getattr__(self, name):
        return getattr(self.element, name)

    def __getitem__(self, name):
        path = self._process_path(path)
        return self.element[name]

    def __iter__(self):
        for node in self.element:
            yield _SOAPElement(node, self.ns_shorthands)

    def __contains__(self, node):
        return node in self.element

    def __repr__(self):
        return "<SOAPElement name=\"%s\">" % (self.element.tag,)

    def _process_path(self, path):
        for sh, ns in self.ns_shorthands.iteritems():
            path = path.replace("/%s:" % sh, "/{%s}" % ns)
            if path.startswith("%s:" % sh):
                path = path.replace("%s:" % sh, "{%s}" % ns, 1)
        return path

    def find(self, path):
        path = self._process_path(path)
        
        node = self.element.find(path)
        if node is None:
            return None
        return _SOAPElement(node, self.ns_shorthands)

    def findall(self, path):
        path = self._process_path(path)
        
        result = []
        nodes = self.element.findall(path)
        for node in nodes:
            result.append(_SOAPElement(node, self.ns_shorthands))
        return result

    def findtext(self, path, type=None):
        result = self.find(path)
        if result is None:
            return ""
        result = result.text
        
        if type is None:
            return result
        return getattr(XMLTYPE, type).decode(result)


class SOAPResponse(object):
    NS_SHORTHANDS = {'soap' : XMLNS.SOAP.ENVELOPE,
            "xmlenc" : XMLNS.ENCRYPTION.BASE,
            "wsse" : XMLNS.WS.SECEXT,
            "wst" : XMLNS.WS.TRUST,
            "wsa" : XMLNS.WS.ADDRESSING,
            "wsp" : XMLNS.WS.POLICY,
            "wsi" : XMLNS.WS.ISSUE,
            "wsu" : XMLNS.WS.UTILITY,
            "ps" : XMLNS.MICROSOFT.PASSPORT,
            "ab" : XMLNS.MICROSOFT.LIVE.ADDRESSBOOK,
            "st" : XMLNS.MICROSOFT.LIVE.STORAGE,
            "oim" : XMLNS.MICROSOFT.LIVE.OIM,
            "rsi" : XMLNS.MICROSOFT.LIVE.RSI }

    def __init__(self, soap_data):
        try:
            tree = self._parse(soap_data)
            self.tree = _SOAPElement(tree, self.NS_SHORTHANDS)
            self.header = self.tree.find("soap:Header")
            self.body = self.tree.find("soap:Body")
            self.fault = self.tree.find("soap:Fault")
        except:
            self.tree = None
            self.header = None
            self.body = None
            self.fault = None
            logger.warning("SOAPResponse: Invalid xml+soap data")

    def __getitem__(self, name):
        return self.tree[name]

    def find(self, path):
        return self.tree.find(path)

    def findall(self, path):
        return self.tree.findall(path)
    
    def findtext(self, path, type=None):
        return self.tree.findtext(path, type)

    def is_fault(self):
        return self.fault is not None

    def is_valid(self):
        return self.tree is not None and self.header is not None

    def _parse(self, data):
        events = ("start", "end", "start-ns", "end-ns")
        ns = []
        data = StringIO.StringIO(data)
        context = ElementTree.iterparse(data, events=events)
        for event, elem in context:
            if event == "start-ns":
                ns.append(elem)
            elif event == "end-ns":
                ns.pop()
            elif event == "start":
                elem.set("(xmlns)", tuple(ns))
        data.close()
        return context.root


class SOAPService(object):

    def __init__(self, name, proxies=None):
        self._name = name
        self._service = getattr(description, self._name)
        self._active_transports = {}
        self._proxies = proxies or {}

    def _send_request(self, name, url, soap_header, soap_body, soap_action,
            callback, errback=None, transport_headers={}, user_data=None):
        
        scheme, host, port, resource = url_split(url)
        http_headers = transport_headers.copy()
        if soap_action is not None:
            http_headers["SOAPAction"] = str(soap_action)
        http_headers["Content-Type"] = "text/xml; charset=utf-8"
        http_headers["Cache-Control"] = "no-cache"
        http_headers["Accept"] = "text/*"
        http_headers["Proxy-Connection"] = "Keep-Alive"
        http_headers["Connection"] = "Keep-Alive"

        request = compress_xml(soap_template % (soap_header, soap_body))

        transport = self._get_transport(name, scheme, host, port,
                callback, errback, user_data)
        transport.request(resource, http_headers, request, 'POST')

    def _response_handler(self, transport, http_response):
        logger.debug("<<< " + str(http_response))
        soap_response = SOAPResponse(http_response.body)
        request_id, callback, errback, user_data = self._unref_transport(transport)

        if not soap_response.is_valid():
            logger.warning("Invalid SOAP Response")
            return #FIXME: propagate the error up

        if not soap_response.is_fault():
            handler = getattr(self,
                    "_Handle" + request_id + "Response",
                    None)
            method = getattr(self._service, request_id)
            response = method.process_response(soap_response)
            
            if handler is not None:
                handler(callback, errback, response, user_data)
            else:
                self._HandleUnhandledResponse(request_id, callback, errback,
                        response, user_data)
        else:
            self._HandleSOAPFault(request_id, callback, errback, soap_response,
                    user_data)

    def _request_handler(self, transport, http_request):
        logger.debug(">>> " + str(http_request))

    def _error_handler(self, transport, error):
        logger.warning("Transport Error :" + str(error))
        request_id, callback, errback = self._unref_transport(transport)
        return request_id, callback, errback #FIXME: do something sensible here

    # Handlers
    def _HandleSOAPFault(self, request_id, callback, errback,
            soap_response, user_data):
        logger.warning("Unhandled SOAPFault to %s" % request_id)

    def _HandleUnhandledResponse(self, request_id, callback, errback,
            response, user_data):
        logger.warning("Unhandled Response to %s" % request_id)

    # Transport management
    def _get_transport(self, request_id, scheme, host, port,
            callback, errback, user_data):
        key = (scheme, host, port)
        if key in self._active_transports:
            trans = self._active_transports[key]
            transport = trans[0]
            trans[1].append((request_id, callback, errback, user_data))
        else:
            proxy = self._proxies.get(scheme, None)
            transport = pymsn.gnet.protocol.ProtocolFactory(scheme,
                    host, port, proxy=proxy)
            handler_id = [transport.connect("response-received",
                    self._response_handler),
                transport.connect("request-sent", self._request_handler),
                transport.connect("error", self._error_handler)]

            trans = [transport, [(request_id, callback, errback, user_data)], handler_id]
            self._active_transports[key] = trans
        return transport

    def _unref_transport(self, transport):
        for key, trans in self._active_transports.iteritems():
            if trans[0] == transport:
                response = trans[1].pop(0)
                
                if len(trans[1]) != 0:
                    return response

                for handle in trans[2]:
                    transport.disconnect(handle)
                del self._active_transports[key]
                return response
        return None

