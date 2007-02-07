#!/usr/bin/env python

import sys
import gobject
import signal
from pymsn.gnet.io import SSLTCPClient
from pymsn.gnet.constants import *

DEFAULT_REQUEST_VARIANT = "canonical"

class DumbPassportClient:
    REQUEST_VARIANTS = {
        "canonical":
        (
            'POST /RST.srf HTTP/1.1\r\n' +
            'Accept: text/*\r\n' +
            'User-Agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; IDCRL 4.100.313.1; IDCRL-cfg 4.0.5633.0; App msnmsgr.exe, 8.1.168.0, {7108E71A-9926-4FCB-BCC9-9A9D3F32E423})\r\n' +
            'Host: login.live.com\r\n' +
            'Content-Length: %d\r\n' +
            'Connection: Keep-Alive\r\n' +
            'Cache-Control: no-cache\r\n' +
            '\r\n',

            '<?xml version="1.0" encoding="UTF-8"?>' +
            '<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsse="http://schemas.xmlsoap.org/ws/2003/06/secext" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/03/addressing" xmlns:wssc="http://schemas.xmlsoap.org/ws/2004/04/sc" xmlns:wst="http://schemas.xmlsoap.org/ws/2004/04/trust">' +
                '<Header>' +
                    '<ps:AuthInfo xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="PPAuthInfo">' +
                        '<ps:HostingApp>{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}</ps:HostingApp>' +
                        '<ps:BinaryVersion>4</ps:BinaryVersion>' +
                        '<ps:UIVersion>1</ps:UIVersion>' +
                        '<ps:Cookies></ps:Cookies>' +
                        '<ps:RequestParams>AQAAAAIAAABsYwQAAAAxMDQ0</ps:RequestParams>' +
                    '</ps:AuthInfo>' +
                    '<wsse:Security>' +
                        '<wsse:UsernameToken Id="user">' +
                            '<wsse:Username>%s</wsse:Username>' +
                            '<wsse:Password>%s</wsse:Password>' +
                        '</wsse:UsernameToken>' +
                    '</wsse:Security>' +
                '</Header>' +
                '<Body>' +
                    '<ps:RequestMultipleSecurityTokens xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="RSTS">' +
                        '<wst:RequestSecurityToken Id="RST0">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>http://Passport.NET/tb</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                        '</wst:RequestSecurityToken>' +
                        '<wst:RequestSecurityToken Id="RST1">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>messengerclear.live.com</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                            '<wsse:PolicyReference URI="MBI_KEY_OLD"></wsse:PolicyReference>' +
                        '</wst:RequestSecurityToken>' +
                        '<wst:RequestSecurityToken Id="RST2">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>messenger.msn.com</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                            '<wsse:PolicyReference URI="?id=507"></wsse:PolicyReference>' +
                        '</wst:RequestSecurityToken>' +
                        '<wst:RequestSecurityToken Id="RST3">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>contacts.msn.com</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                            '<wsse:PolicyReference URI="MBI"></wsse:PolicyReference>' +
                        '</wst:RequestSecurityToken>' +
                        '<wst:RequestSecurityToken Id="RST4">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>messengersecure.live.com</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                            '<wsse:PolicyReference URI="MBI_SSL"></wsse:PolicyReference>' +
                        '</wst:RequestSecurityToken>' +
                        '<wst:RequestSecurityToken Id="RST5">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>spaces.live.com</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                            '<wsse:PolicyReference URI="MBI"></wsse:PolicyReference>' +
                        '</wst:RequestSecurityToken>' +
                        '<wst:RequestSecurityToken Id="RST6">' +
                            '<wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>' +
                            '<wsp:AppliesTo>' +
                                '<wsa:EndpointReference>' +
                                    '<wsa:Address>storage.msn.com</wsa:Address>' +
                                '</wsa:EndpointReference>' +
                            '</wsp:AppliesTo>' +
                            '<wsse:PolicyReference URI="MBI"></wsse:PolicyReference>' +
                        '</wst:RequestSecurityToken>' +
                    '</ps:RequestMultipleSecurityTokens>' +
                '</Body>' +
            '</Envelope>'
        ),

        "pymsn":
        (
            'POST /RST.srf HTTP/1.1\r\n' +
            'Host: login.live.com:443\r\n' +
            'Content-Type: text/xml; charset=utf-8\r\n' +
            'Content-Length: %d\r\n' +
            'Accept: text/*\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; IDCRL 4.100.313.1; IDCRL-cfg 4.0.5633.0; App MsnMsgr.Exe, 8.1.168.0, {7108E71A-9926-4FCB-BCC9-9A9D3F32E423})\r\n' +
            '\r\n',

            '<?xml version="1.0" encoding="utf-8"?>' +
            '<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/">' +
                '<ns0:Header>' +
                    '<ns1:AuthInfo Id="PPAuthInfo" xmlns:ns1="http://schemas.microsoft.com/Passport/SoapServices/PPCRL">' +
                        '<ns1:HostingApp>{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}</ns1:HostingApp>' +
                        '<ns1:BinaryVersion>4</ns1:BinaryVersion>' +
                        '<ns1:UIVersion>1</ns1:UIVersion>' +
                        '<ns1:Cookies />' +
                        '<ns1:RequestParams>AQAAAAIAAABsYwQAAAAxMDMz</ns1:RequestParams>' +
                    '</ns1:AuthInfo>' +
                    '<ns1:Security xmlns:ns1="http://schemas.xmlsoap.org/ws/2003/06/secext">' +
                        '<ns1:UsernameToken Id="user">' +
                            '<ns1:Username>%s</ns1:Username>' +
                            '<ns1:Password>%s</ns1:Password>' +
                        '</ns1:UsernameToken>' +
                    '</ns1:Security>' +
                '</ns0:Header>' +
                '<ns0:Body>' +
                    '<ns1:RequestMultipleSecurityTokens Id="RSTS" ns0:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://schemas.microsoft.com/Passport/SoapServices/PPCRL">' +
                        '<ns2:RequestSecurityToken Id="RST0" xmlns:ns2="http://schemas.xmlsoap.org/ws/2004/04/trust">' +
                            '<ns2:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</ns2:RequestType>' +
                            '<ns3:AppliesTo xmlns:ns3="http://schemas.xmlsoap.org/ws/2002/12/policy">' +
                                '<ns4:EndpointReference xmlns:ns4="http://schemas.xmlsoap.org/ws/2004/03/addressing">' +
                                    '<ns4:Address>messengerclear.live.com</ns4:Address>' +
                                '</ns4:EndpointReference>' +
                            '</ns3:AppliesTo>' +
                            '<ns3:PolicyReference URI="MBI_KEY_OLD" xmlns:ns3="http://schemas.xmlsoap.org/ws/2003/06/secext" />' +
                        '</ns2:RequestSecurityToken>' +
                    '</ns1:RequestMultipleSecurityTokens>' +
                '</ns0:Body>' +
            '</ns0:Envelope>'
        ),

        "testing":
        (
            'POST /RST.srf HTTP/1.1\r\n' +
            'Host: login.live.com:443\r\n' +
            'Content-Type: text/xml; charset=utf-8\r\n' +
            'Content-Length: %d\r\n' +
            'Accept: text/*\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; IDCRL 4.100.313.1; IDCRL-cfg 4.0.5633.0; App MsnMsgr.Exe, 8.1.168.0, {7108E71A-9926-4FCB-BCC9-9A9D3F32E423})\r\n' +
            '\r\n',

            '<?xml version="1.0" encoding="utf-8"?>' +
            '<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/">' +
                '<ns0:Header>' +
                    '<ns1:AuthInfo Id="PPAuthInfo" xmlns:ns1="http://schemas.microsoft.com/Passport/SoapServices/PPCRL">' +
                        '<ns1:HostingApp>{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}</ns1:HostingApp>' +
                        '<ns1:BinaryVersion>4</ns1:BinaryVersion>' +
                        '<ns1:UIVersion>1</ns1:UIVersion>' +
                        '<ns1:Cookies />' +
                        '<ns1:RequestParams>AQAAAAIAAABsYwQAAAAxMDMz</ns1:RequestParams>' +
                    '</ns1:AuthInfo>' +
                    '<ns1:Security xmlns:ns1="http://schemas.xmlsoap.org/ws/2003/06/secext">' +
                        '<ns1:UsernameToken Id="user">' +
                            '<ns1:Username>%s</ns1:Username>' +
                            '<ns1:Password>%s</ns1:Password>' +
                        '</ns1:UsernameToken>' +
                    '</ns1:Security>' +
                '</ns0:Header>' +
                '<ns0:Body>' +
                    '<ns1:RequestMultipleSecurityTokens Id="RSTS" ns0:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://schemas.microsoft.com/Passport/SoapServices/PPCRL">' +
                        '<ns2:RequestSecurityToken Id="RST0" xmlns:ns2="http://schemas.xmlsoap.org/ws/2004/04/trust">' +
                            '<ns2:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</ns2:RequestType>' +
                            '<ns3:AppliesTo xmlns:ns3="http://schemas.xmlsoap.org/ws/2002/12/policy">' +
                                '<ns4:EndpointReference xmlns:ns4="http://schemas.xmlsoap.org/ws/2004/03/addressing">' +
                                    '<ns4:Address>http://Passport.NET/tb</ns4:Address>' +
                                '</ns4:EndpointReference>' +
                            '</ns3:AppliesTo>' +
                        '</ns2:RequestSecurityToken>' +
                        '<ns2:RequestSecurityToken Id="RST1" xmlns:ns2="http://schemas.xmlsoap.org/ws/2004/04/trust">' +
                            '<ns2:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</ns2:RequestType>' +
                            '<ns3:AppliesTo xmlns:ns3="http://schemas.xmlsoap.org/ws/2002/12/policy">' +
                                '<ns4:EndpointReference xmlns:ns4="http://schemas.xmlsoap.org/ws/2004/03/addressing">' +
                                    '<ns4:Address>messengerclear.live.com</ns4:Address>' +
                                '</ns4:EndpointReference>' +
                            '</ns3:AppliesTo>' +
                            '<ns3:PolicyReference URI="MBI_KEY_OLD" xmlns:ns3="http://schemas.xmlsoap.org/ws/2003/06/secext" />' +
                        '</ns2:RequestSecurityToken>' +
                    '</ns1:RequestMultipleSecurityTokens>' +
                '</ns0:Body>' +
            '</ns0:Envelope>'
        ),
    }

    def __init__(self, account, password, request_variant):
        client = SSLTCPClient("login.live.com", 443)
        client.connect("notify::status", self._status_changed_cb)
        client.connect("error", self._error_cb)
        client.connect("received", self._received_cb)
        client.connect("sent", self._sent_cb)
        self._client = client
        self.__account = account
        self.__password = password
        self.__variant = self.REQUEST_VARIANTS[request_variant]

    def start(self):
        self._client.open()
        
    def _status_changed_cb(self, *args):
        status = self._client.get_property("status")
        print "DumbPassportClient._status_changed_cb: %s" % \
            self._io_status_to_string(status)
        if status == IoStatus.OPEN:
            self.__body = self.__variant[1] % (self.__account, self.__password)
            self._client.send(self.__variant[0] % len(self.__body), self.__headers_sent_cb)
        elif status == IoStatus.CLOSED:
            mainloop.quit()

    def __headers_sent_cb(self):
        self._client.send(self.__body)

    def _io_status_to_string(self, status):
        if status == IoStatus.CLOSING:
            return "IoStatus.CLOSING"
        elif status == IoStatus.CLOSED:
            return "IoStatus.CLOSED"
        elif status == IoStatus.OPENING:
            return "IoStatus.OPENING"
        elif status == IoStatus.OPEN:
            return "IoStatus.OPEN"
        else:
            return "IoStatus.UNKNOWN"

    def _error_cb(self, client, error):
        print "DumbPassportClient._error_cb: %d" % error

    def _received_cb(self, client, data, data_length):
        print "DumbPassportClient._received_cb: '%s'" % data

    def _sent_cb(self, client, data, data_length):
        print "DumbPassportClient._sent_cb: '%s'" % data


if __name__ == "__main__":
    def quit():
        mainloop.quit()
    
    def sigterm_cb():
        gobject.idle_add(quit)
    
    if len(sys.argv) not in (3, 4):
        print >> sys.stderr, "usage: %s ACCOUNT PASSWORD [request_variant]" % sys.argv[0]
        sys.exit(1)
    
    if len(sys.argv) == 4:
        request_variant = sys.argv[3]
    else:
        request_variant = DEFAULT_REQUEST_VARIANT
    
    signal.signal(signal.SIGTERM, sigterm_cb)
    global mainloop
    mainloop = gobject.MainLoop()
    
    client = DumbPassportClient(sys.argv[1], sys.argv[2], request_variant)
    client.start()

    try:
        mainloop.run()
    except KeyboardInterrupt:
        quit()