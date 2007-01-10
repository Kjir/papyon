import sys, os
parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir) 
del parent_dir
del sys
del os

import gnet.message.SOAP as SOAP
import service.SOAPService as SOAPService
import service.SingleSignOn as SSO

NS_MSNAB = "http://www.msn.com/webservices/AddressBook"

request = SOAP.SOAPRequest("ABFindAll", NS_MSNAB)
ABApplicationHeader = request.add_header("ABApplicationHeader", NS_MSNAB)
ABApplicationHeader.append("ApplicationId", value="09607671-1C32-421F-A6A6-CBFAA51AB5F4")
ABApplicationHeader.append("IsMigration", value="false")
ABApplicationHeader.append("PartnerScenario", value="Initial")

ABAuthHeader = request.add_header("ABAuthHeader", NS_MSNAB)
ABAuthHeader.append("ManagedGroupRequest", value="false")

request.add_argument("abId", value="00000000-0000-0000-0000-000000000000")
request.add_argument("abView", value="Full")
request.add_argument("deltasOnly", value="true")
request.add_argument("lastChange", value="0001-01-01T00:00:00.0000000-08:00")

print request
print "------------------------------------------------"

response = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Header>
        <ServiceHeader xmlns="http://www.msn.com/webservices/AddressBook">
            <Version>11.01.0922.0000</Version>
        </ServiceHeader>
    </soap:Header>
    <soap:Body>
        <ABFindAllResponse xmlns="http://www.msn.com/webservices/AddressBook">
            <ABFindAllResult>
                <contacts>
                    <Contact>
                        <contactId> Removed </contactId>
                        <contactInfo>
                            <annotations>
                                <Annotation>
                                    <Name>MSN.IM.MBEA</Name>
                                    <Value>0</Value>
                                </Annotation>
                                <Annotation>
                                    <Name>MSN.IM.GTC</Name>
                                    <Value>1</Value>
                                </Annotation>
                                <Annotation>
                                    <Name>MSN.IM.BLP</Name>
                                    <Value>0</Value>
                                </Annotation>
                            </annotations>
                            <contactType>Me</contactType>
                            <quickName>Q</quickName>
                            <passportName> Removed </passportName>
                            <IsPassportNameHidden>false</IsPassportNameHidden>
                            <displayName>Inky | Hello, World from WLM</displayName>
                            <puid>0</puid>
                            <CID>0</CID>
                            <IsNotMobileVisible>false</IsNotMobileVisible>
                            <isMobileIMEnabled>false</isMobileIMEnabled>
                            <isMessengerUser>false</isMessengerUser>
                            <isFavorite>false</isFavorite>
                            <isSmtp>false</isSmtp>
                            <hasSpace>true</hasSpace>
                            <spotWatchState>NoDevice</spotWatchState>
                            <birthdate>0001-01-01T00:00:00.0000000-08:00</birthdate>
                            <primaryEmailType>ContactEmailPersonal</primaryEmailType>
                            <PrimaryLocation>ContactLocationPersonal</PrimaryLocation>
                            <PrimaryPhone>ContactPhonePersonal</PrimaryPhone>
                            <IsPrivate>false</IsPrivate>
                            <Gender>Unspecified</Gender>
                            <TimeZone>None</TimeZone>
                        </contactInfo>
                        <propertiesChanged/>
                        <fDeleted>false</fDeleted>
                        <lastChange>2005-11-11T15:55:03.2600000-08:00</lastChange>
                    </Contact>
                </contacts>
                <ab>
                    <abId>00000000-0000-0000-0000-000000000000</abId>
                    <abInfo>
                        <ownerPuid>0</ownerPuid>
                        <OwnerCID>0</OwnerCID>
                        <ownerEmail> Removed </ownerEmail>
                        <fDefault>true</fDefault>
                        <joinedNamespace>false</joinedNamespace>
                    </abInfo>
                    <lastChange>2005-11-11T15:55:03.2600000-08:00</lastChange>
                    <DynamicItemLastChanged>2005-11-09T09:16:56.2970000-08:00</DynamicItemLastChanged>
                    <createDate>2003-07-14T15:46:20.6500000-07:00</createDate>
                    <propertiesChanged />
                </ab>
           </ABFindAllResult>
       </ABFindAllResponse>
   </soap:Body>
</soap:Envelope>"""

response = SOAP.SOAPResponse(response)
print response.body.find(".//{%s}displayName" % NS_MSNAB).text

print "------------------------------------------------"
class TestService(SOAPService.SOAPService):
    def __init__(self, url):
        SOAPService.SOAPService.__init__(self, url)

    def _soap_action(self, method):
        return "http://www.test.org#%s" % method

    def _method_namespace(self, method):
        return "http://www.test.org/SOAP/TestService"

test = TestService("http://www.test.org")
test.ABFindAll(("abId", "00000000-0000-0000-0000-000000000000"),
		("abView","abView"),
		("deltasOnly","true"),
		("lastChange","0001-01-01T00:00:00.0000000-08:00"))

print '------------------------------------------------'
sso = SSO.SingleSignOn("kimbix@hotmail.com", "linox46")
sso.RequestMultipleSecurityTokens(SSO.LiveService.TB, SSO.LiveService.MESSENGER_CLEAR)
