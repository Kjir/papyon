import gnet.message.SOAP as SOAP

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

