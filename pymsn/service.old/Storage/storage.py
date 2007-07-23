# -*- coding: utf-8 -*-
#
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from pymsn.service.SOAPService import SOAPService, SOAPUtils, SOAPFault

STORAGE_SERVICE_URL = "http://storage.msn.com/storageservice/SchematizedStore.asmx"
NS_STORAGE = "http://www.msn.com/webservices/storage/w10"

NS_SHORTHANDS = { "ss" : NS_STORAGE }

class StorageError(SOAPFault):
    def __init__(self, xml_node):
        SOAPFault.__init__(self, xml_node)

class StorageService(BaseStorage, SOAPService):
    
    def __init__(self, storage_security_token):
        BaseStorage.__init__(self, storage_security_token)
        SOAPService.__init__(self, STORAGE_SERVICE_URL)

    
    def GetProfile(self, scenario, cid, callback, *callback_args):
        """call the GetProfile SOAP action
        
            @param scenario: the scenario to use for the action
            @type scenario: string in {"Initial", 
                                       "RoamingIdentityChanged"}

            @param cid: the contact id
            @type cid: string
        """
        self.__scenario = scenario
        self._method("GetProfile", callback, *callback_args, {})
        profileHandle = self.request.add_argument("profileHandle", NS_STORAGE)
        Alias = profileHandle.append("Alias", NS_STORAGE)
        Alias.append("Name", NS_STORAGE, value=cid)
        Alias.append("NameSpace", NS_STORAGE, value="MyCidStuff")
        profileHandle.append("RelationshipName", NS_STORAGE, value="MyProfile")
        profileAttributes = self.request.add_argument("profileAttributes", NS_STORAGE)
        profileAttributes.append("ResourceID", NS_STORAGE, value="true")
        profileAttributes.append("DateModified", NS_STORAGE, value="true")
        ExpressionProfileAttributes = profileAttributes.\
            append("ExpressionProfileAttributes", NS_STORAGE)
        ExpressionProfileAttributes.append("ResourceID", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("DateModified", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("DisplayName", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("DisplayNameLastModified", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("PersonalStatus", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("PersonalStatusLastModified", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("StaticUserTilePublicURL", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("Photo", NS_STORAGE, value="true")
        ExpressionProfileAttributes.append("Flags", NS_STORAGE, value="true")
        self.send_request()

    def UpdateProfile(self, scenario, rid, fields, flag,
                      callback, *callback_args):
        """call the UpdateProfile SOAP action

            @param scenario: the scenario to use for the action
            @type scenario: string in {"RoamingIdentityChanged"}

            @param rid: resource id
            @type rid: string

            @param fields: fields to update
            @type fields: <key:string,value:string> dict with
                          key in {"DisplayName", "PersonalStatus"}
                          and string values

            @param flags: flag, observed as 0 or 1 (when fields is empty?)            
        """
        self.__scenario = scenario
        self._method("UpdateProfile", callback, *callback_args, {})
        profile = self.request.add_argument("profile", NS_STORAGE)
        profile.append("ResourceID", NS_STORAGE, value=rid)
        ExpressionProfile = profile.append("ExpressionProfile", NS_STORAGE)
        ExpressionProfile.append("FreeText", NS_STORAGE, value="Update")
        for field, nvalue in fields.iteritems():
            ExpressionProfile.append(field, NS_STORAGE, value=nvalue)
        ExpressionProfile.append("Flags", NS_STORAGE, value=flags)
        self.send_request()

    def CreateRelationships(self, scenario, sourceid, sourcetype,
                            targetid, targettype, relationship,
                            callback, *callback_args):
        """call the CreateRelationships SOAP action

            @param scenario: the scenario to use for the action
            @type scenario: string in {"RoamingIdentityChanged"}
        """
        self.__scenario = scenario
        self._method("CreateRelationships", callback, *callback_args, {})
        Relationship = self.request.add_argument("relationships", NS_STORAGE).\
            append("Relationship", NS_STORAGE)
        Relationship.append("SourceID", NS_STORAGE, value=sourceid)
        Relationship.append("SourceType", NS_STORAGE, value=sourcetype)
        Relationship.append("TargetID", NS_STORAGE, value=targetid)
        Relationship.append("TargetType", NS_STORAGE, value=targettype)
        Relationship.append("RelationshipName", NS_STORAGE, value=relationship)
        self.send_request()


    def DeleteRelationships(self, scenario, relationship, cid, target_rid
                            callback, *callback_args):
        """call the DeleteRelationships SOAP action

            @param scenario: the scenario to use for the action
            @type scenario: string in {"RoamingIdentityChanged"}

            @param relationship: name of the relationship to delete
            @type relationship: string in {"/UserTiles"}

            @param cid: the contact id
            @type cid: string

            @param rid: the resource id
            @type rid: string
        """
        self.__scenario = scenario
        self._method("DeleteRelationships", callback, *callback_args, {})
        sourceHandle = self.request.add_argument("sourceHandle", NS_STORAGE)

        sourceHandle.append("RelationshipName", NS_STORAGE, value=relationship)
        Alias = sourceHandle.append("Alias", NS_STORAGE)
        Alias.append("Name", NS_STORAGE, value=cid)
        Alias.append("NameSpace", NS_STORAGE, value="MyCidStuff")
        
        targetHandles = self.request.add_argument("targetHandles", NS_STORAGE)
        targetHandles.append("ObjectHandle", NS_STORAGE).\
            append("ResourceID", NS_STORAGE, value=rid)
        self.send_request()

    def DeleteRelationships(self, scenario, source_rid, target_rid,
                            callback, *callback_args):
        self.__scenario = scenario
        self._method("DeleteRelationships", callback, *callback_args, {})
        self.request.add_argument("sourceHandle", NS_STORAGE).\
            append("ResourceID", NS_STORAGE, value=source_rid)
        targetHandles = self.request.add_argument("targetHandles", NS_STORAGE)
        targetHandles.append("ObjectHandle", NS_STORAGE).\
            append("ResourceID", NS_STORAGE, value=target_rid)
        self.send_request()

    def CreateDocument(self, scenario, cid, name, type, data,
                       callback, *callback_args):
        self.__scenario = scenario
        self._method("CreateDocument", callback, *callback_args, {})
        parentHandle = self.request.add_argument("parentHandle", NS_STORAGE)
        parentHandle.append("RelationshipName", NS_STORAGE, value="/UserTiles")
        Alias = parentHandle.append("Alias", NS_STORAGE)
        Alias.append("Name", NS_STORAGE, value=cid)
        Alias.append("NameSpace", NS_STORAGE, value="MyCidStuff")
        document = self.request.add_argument("document", NS_STORAGE, type="Photo")
        document.append("Name", NS_STORAGE, value=name)
        DocumentStream = document.append("DocumentStreams", NS_STORAGE).\
            append("DocumentStream", NS_STORAGE, { "type" : "PhotoStream" })
        DocumentStream.append("DocumentStreamType", NS_STORAGE, value="UserTileStatic")
        DocumentStream.append("MimeType", NS_STORAGE, value=type)
        DocumentStream.append("Data", NS_STORAGE, value=data)
        DocumentStream.append("DataSize", NS_STORAGE, value="0")
        self.request.add_argument("relationshipName", NS_STORAGE, 
                                  value="Messenger User Tile")
        self.send_request()

    def FindDocuments(self, scenario, cid,
                      callback, *callback_args):
        self.__scenario = scenario
        self._method("FindDocuments", callback, *callback_args, {})
        objectHandle = self.request.add_argument("objectHandle", NS_STORAGE)
        objectHandle.append("RelationshipName", NS_STORAGE, value="/UserTiles")
        Alias = parentHandle.append("Alias", NS_STORAGE)
        Alias.append("Name", NS_STORAGE, value=cid)
        Alias.append("NameSpace", NS_STORAGE, value="MyCidStuff")
        documentAttributes = self.request.add_argument("documentAttributes", NS_STORAGE)
        documentAttributes.append("ResourceID", NS_STORAGE, value="true")
        documentAttributes.append("Name", NS_STORAGE, value="true")
        self.request.add_argument("documentFilter", NS_STORAGE).\
            append("FilterAttributes", NS_STORAGE, value="None")
        self.request.add_argument("documentSort", NS_STORAGE).\
            append("SortBy", NS_STORAGE, value="DateModified")
        findContext = self.request.add_argument("findContext", NS_STORAGE)
        findContext.append("FindMethod", NS_STORAGE, value="Default")
        findContext.append("ChunkSize", NS_STORAGE, value="25")
        self.send_request()

    def _extract_response(self, method, soap_response):
        path = "./%sResponse".replace("/", "/{%s}" % NS_STORAGE) % method
        if soap_response.body.find(path) is None: 
            raise StorageError(soap_response.body)

        if method == "GetProfile":
            # TODO : grab data in the response
            return (soap_response,)
        if method == "UpdateProfile":
            return (soap_response,)
        if method == "CreateRelationships":
            return (soap_response,)
        if method == "DeleteRelationships":
            return (soap_response,)
        if method == "CreateDocument":
            path = "./CreateDocumentResponse/CreateDocumentResult".\
                replace("/", "/{%s}" % NS_STORAGE)
            rid =  soap_response.body.find(path)
            return (soap_response, rid.text)
        if method == "FindDocuments":
            path = "./FindDocumentsResponse/FindDocumentsResult/Document/ResourceID".\
                replace("/", "/{%s}" % NS_STORAGE)
            rid =  soap_response.body.find(path)
            path = "./FindDocumentsResponse/FindDocumentsResult/Document/Name".\
                replace("/", "/{%s}" % NS_STORAGE)
            name =  soap_response.body.find(path)
            return (soap_response, rid.text, name.text)
        else:
            return SOAPService._extract_response(self, method, soap_response)
