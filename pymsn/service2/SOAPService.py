# -*- coding: utf-8 -*-
#
# pymsn - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

space_regex = [(re.compile('>\s+<'), '><'),
        (re.compile('>\s+'), '>'),
        (re.compile('<\s+'), '<')]

def compress_xml(xml_string):
    global space_regex
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


class XMLNS(object):

    class SOAP(object):
        ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"
        ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"
        ACTOR_NEXT = "http://schemas.xmlsoap.org/soap/actor/next"
    
    class SCHEMA(object):
        XSD1 = "http://www.w3.org/1999/XMLSchema"
        XSD2 = "http://www.w3.org/2000/10/XMLSchema"
        XSD3 = "http://www.w3.org/2001/XMLSchema"
        
        XSI1 = "http://www.w3.org/1999/XMLSchema-instance"
        XSI2 = "http://www.w3.org/2000/10/XMLSchema-instance"
        XSI3 = "http://www.w3.org/2001/XMLSchema-instance"

    class ENCRYPTION(object):
        BASE = "http://www.w3.org/2001/04/xmlenc#"
    
    class WS:
        SECEXT = "http://schemas.xmlsoap.org/ws/2003/06/secext"
        TRUST = "http://schemas.xmlsoap.org/ws/2004/04/trust"
        ADDRESSING = "http://schemas.xmlsoap.org/ws/2004/03/addressing"
        POLICY = "http://schemas.xmlsoap.org/ws/2002/12/policy"
        ISSUE = "http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue"
        UTILITY = "http://docs.oasis-open.org/wss/2004/01/" + \
                "oasis-200401-wss-wssecurity-utility-1.0.xsd"
    
    class MICROSOFT:
        PASSPORT = "http://schemas.microsoft.com/Passport/SoapServices/PPCRL"


class SOAPResponse(object):
    NS_SHORTHANDS = {'soap' : XMLNS.SOAP.ENVELOPE,
            "xmlenc" : XMLNS.ENCRYPTION.BASE,
            "wsse" : XMLNS.WS.SECEXT,
            "wst" : XMLNS.WS.TRUST,
            "wsa" : XMLNS.WS.ADDRESSING,
            "wsp" : XMLNS.WS.POLICY,
            "wsi" : XMLNS.WS.ISSUE,
            "wsu" : XMLNS.WS.UTILITY,
            "ps" : XMLNS.MICROSOFT.PASSPORT}

    class _SOAPElement(object):
        def __init__(self, element, ns_shorthands):
            self.element = element
            self.ns_shorthands = ns_shorthands.copy()

        def __getattr__(self, name):
            return getattr(self.element, name)

        def find(self, path):
            for sh, ns in self.ns_shorthands.iteritems():
                path = path.replace("/%s:" % sh, "/{%s}" % ns)
            return _SOAPElement(self.element.find(path), self.ns_shorthands)


    def __init__(self, soap_data):
        self.tree = _SOAPElement(self._parse(data), NS_SHORTHANDS)
        self.header = self.tree.find("soap:Header")
        self.body = self.tree.find("soap:Body")

    def find(self, path):
        return self.tree.find(path)

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

    def _send_request(self, url, soap_header, soap_body, soap_action,
            callback, errback=None, transport_headers={}):
        
        scheme, host, port, resource = url_split(url)
        http_headers = transport_headers.copy()
        if soap_action is not None:
            http_headers["SOAPAction"] = str(soap_action)
        http_headers["Content-Type"] = "text/xml; charset=utf-8"
        http_headers["Cache-Control"] ="no-cache"
        http_headers["Accept"] = "text/*"
        http_headers["Proxy-Connection"] = "Keep-Alive"
        http_headers["Connection"] = "Keep-Alive"

        request = compress_xml(soap_template % (soap_header, soap_body))

        transport = self._get_transport(scheme, host, port, callback, errback)
        transport.request(resource, http_headers, request, 'POST')

    def _response_handler(self, transport, http_response):
        logger.debug("<<< " + str(http_response))
        return self._unref_transport(transport)

    def _request_handler(self, transport, http_request):
        logger.debug(">>> " + str(http_request))

    def _error_handler(self, transport, error):
        logger.warning("Transport Error :" + str(error))
        return self._unref_transport(transport)

    def _get_transport(self, scheme, host, port, callback, errback):
        key = (scheme, host, port)
        if key in self._active_transports:
            trans = self._active_transports[key]
            transport = trans[0]
            trans[1].append((callback, errback)) # increment the usage
        else:
            proxy = self._proxies.get(scheme, None)
            transport = pymsn.gnet.protocol.ProtocolFactory(scheme,
                    host, port, proxy=proxy)
            handler_id = [transport.connect("response-received",
                    self._response_handler),
                transport.connect("request-sent", self._request_handler),
                transport.connect("error", self._error_handler)]

            trans = [transport, [(callback, errback)], handler_id]
            self._active_transports[key] = trans
        return transport

    def _unref_transport(self, transport):
        for key, trans in self._active_transports.iteritems():
            if trans[0] == transport:
                callback, errback = trans[1].pop(0)
                
                if len(trans[1]) != 0:
                    return callback, errback

                for handle in trans[2]:
                    transport.disconnect(handle)
                del self._active_transports[key]
                return callback, errback
        return None

