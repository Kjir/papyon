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
import ZSI
import ZSI.client
import ZSI.auth
import ZSI.address

import logging

__all__ = ['SOAPService']

logger = logging.getLogger('Service')

def url_split(self, url, default_scheme='http'):
    from urlparse import urlsplit, urlunsplit
    if "://" not in url: # fix a bug in urlsplit
        url = default_scheme + "://" + url
    protocol, host, path, query, fragment = urlsplit(url)
    if path == "": path = "/"
    try:
        host, port = host.rsplit(":", 1)
    except:
        port = None
    resource = urlunsplit(('', '', path, query, fragment))
    return protocol, host, port, resource


def _SOAPBinding(ZSI.client._Binding):
    def __init__(self, nsdict=None, url=None, soapaction='', proxies=None):
        '''Initialize.
        Keyword arguments include:
            ns_dict -- namespace entries to add
            url -- URL of resource, POST is path 
            soap_action -- value of SOAPAction header
            proxies -- dict mapping protocol to a ProxyInfos instance
        '''
        ZSI.client._Binding.__init__(self, nsdict, transport=None, url=url,
                tracefile=None, readerclass=None, writerclass=None,
                soapaction=soapaction, wsAddressURI=None, sig_handler=None,
                transdict=None)
        self._proxies = proxies or {}
        self._active_transports = {}
        
        del self.RPC
        del self.SendSOAPDataHTTPDigestAuth
        del self.ReceiveRaw
        del self.IsSOAP
        del self.ReceiveSOAP
        del self.IsAFault
        del self.Receive

    def Send(self, url, opname, obj, nsdict={}, soapaction=None, wsaction=None, 
             endPointReference=None, **kw):
        '''Send a message.  If url is None, use the value from the
        constructor (else error). obj is the object (data) to send.
        Data may be described with a requesttypecode keyword, the default 
        is the class's typecode (if there is one), else Any.

        Try to serialize as a Struct, if this is not possible serialize an Array.  If 
        data is a sequence of built-in python data types, it will be serialized as an
        Array, unless requesttypecode is specified.

        arguments:
            url -- 
            opname -- struct wrapper
            obj -- python instance

        key word arguments:
            nsdict -- 
            soapaction --
            wsaction -- WS-Address Action, goes in SOAP Header.
            endPointReference --  set by calling party, must be an 
                EndPointReference type instance.
            requesttypecode -- 

        '''
        url = url or self.url
        endPointReference = endPointReference or self.endPointReference

        # Serialize the object.
        d = {}
        d.update(self.nsdict)
        d.update(nsdict)

        sw = ZSI.SoapWriter(nsdict=d, header=True,
                outputclass=self.writerclass,
                encodingStyle=kw.get('encodingStyle'),)
        
        requesttypecode = kw.get('requesttypecode')
        if kw.has_key('_args'): #NamedParamBinding
            tc = requesttypecode or ZSI.TC.Any(pname=opname, aslist=False)
            sw.serialize(kw['_args'], tc)
        elif not requesttypecode:
            tc = getattr(obj, 'typecode', None) or \
                    ZSI.TC.Any(pname=opname, aslist=False)
            try:
                if type(obj) in _seqtypes:
                    obj = dict(map(lambda i: (i.typecode.pname,i), obj))
            except AttributeError:
                # can't do anything but serialize this in a SOAP:Array
                tc = ZSI.TC.Any(pname=opname, aslist=True)
            else:
                tc = ZSI.TC.Any(pname=opname, aslist=False)

            sw.serialize(obj, tc)
        else:
            sw.serialize(obj, requesttypecode)

        # 
        # Determine the SOAP auth element.  SOAP:Header element
        if self.auth_style & ZSI.auth.AUTH.zsibasic:
            sw.serialize_header(_AuthHeader(self.auth_user, self.auth_pass),
                _AuthHeader.typecode)

        # 
        # Serialize WS-Address
        if self.wsAddressURI is not None:
            if self.soapaction and wsaction.strip('\'"') != self.soapaction:
                raise ZSI.WSActionException, \
                        'soapAction(%s) and WS-Action(%s) must match'\
                        % (self.soapaction,wsaction)

            self.address = ZSI.address.Address(url, self.wsAddressURI)
            self.address.setRequest(endPointReference, wsaction)
            self.address.serialize(sw)

        # 
        # WS-Security Signature Handler
        if self.sig_handler is not None:
            self.sig_handler.sign(sw)

        scheme, host, port, resource = url_split(url)
        transport = self._get_transport(scheme, host, port)

        self.SendSOAPData(transport, str(sw), url, soapaction, **kw)

    def SendSOAPData(self, transport, soapdata, url, soapaction, headers={}, **kw):
        url = url or self.url
        #request_uri = ZSI._get_postvalue_from_absoluteURI(url)
        scheme, host, port, resource = url_split(url)
        
        h = headers.copy()
        h["SOAAction"] = '"%s"' % (soapaction or self.soapaction)
        h["Content-Type"] = 'text/xml; charset=utf-8'
        h["Cache-Control"] ="no-cache"
        h["Accept"] = "text/*"
        # fix : (to be removed later)
        h["Proxy-Connection"] = "Keep-Alive"
        h["Connection"] = "Keep-Alive"

        transport.request(resource, h, soapdata, 'POST')
        self.ps = None

    def _response_handler(self, transport, response):
        logger.debug("<<< " + str(response))
        self.ps = ParsedSoap(response.body, 
                        readerclass=self.readerclass)
        self._unref_transport(transport)

    def _request_handler(self, transport, request):
        logger.debug("<<< " + str(request))

    def _error_handler(self, transport, error):
        logger.warning("Transport Error :" + str(error))
        self._unref_transport(transport)

    def _get_transport(self, scheme, host, port):
        if (scheme, host, port) in self._active_transports:
            trans = self._active_transports[(scheme, host, port)]
            transport = trans[0]
            trans[1] + = 1 # increment the usage
        else:
            proxy = self._proxies.get(scheme, None)
            transport = pymsn.gnet.protocol.ProtocolFactory(scheme,
                    host, port, proxy=proxy)
            trans = [transport, 1, []]
            trans[2].append(transport.connect("response-received", self._response_handler))
            trans[2].append(transport.connect("request-sent", self._request_handler))
            trans[2].append(transport.connect("error", self._error_handler))
            self._active_transports[(scheme, host, port)] = trans
        return transport

    def _unref_transport(self, transport):
        for key, trans in self._active_transports:
            if trans[0] == transport:
                trans[1] -= 1
                if trans[1] == 0:
                    for handle in trans[2]:
                        transport.disconnect(handle)
                    del self._active_transports[key]

