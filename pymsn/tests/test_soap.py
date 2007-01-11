import sys, os
parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir) 
del parent_dir
del sys
del os

import gnet.message.SOAP as SOAP
import service.SOAPService as SOAPService
import service.SingleSignOn as SSO
import gobject

NS_TEMP = "urn:xmethods-Temperature"
class TemperatureService(SOAPService.SOAPService):
    def __init__(self, url):
        SOAPService.SOAPService.__init__(self, url)

    def _soap_action(self, method):
        return ""

    def _method_namespace(self, method):
        return NS_TEMP

#test = TemperatureService("http://services.xmethods.net/soap/servlet/rpcrouter")
#test.getTemp(("string", "zipcode", "10000"))

#print '------------------------------------------------'
sso = SSO.SingleSignOn("kimbix@hotmail.com", "linox45")
sso.RequestMultipleSecurityTokens(SSO.LiveService.TB, SSO.LiveService.MESSENGER_CLEAR)

gobject.MainLoop().run()
