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

from pymsn.service.SOAPService import SOAPService, SOAPUtils

STORAGE_SERVICE_URL = "http://storage.msn.com/storageservice/SchematizedStore.asmx"
NS_STORAGE = "http://www.msn.com/webservices/storage/w10"

NS_SHORTHANDS = { "ss" : NS_STORAGE }

class StorageService(BaseStorage, SOAPService):
    
    def __init__(self, storage_security_token):
        BaseStorage.__init__(self, storage_security_token)
        SOAPService.__init__(self, STORAGE_SERVICE_URL)

    
    def GetProfile(self, scenario, cid, fields, expression_fields, 
                   callback, *callback_args):
        """call the GetProfile SOAP action
        
            @param scenario: the scenario to use for the action
            @type scenario: string in {"Initial", 
                                       "RoamingIdentityChanged"}

            @param cid: the contact id
            @type cid: string

            @param fields: fields to retrieve
            @type fields: <key:string,value:string> dict with
                          key in {"ResourceID", "DateModified"}
                          and value in {"true", "false"}

            @param expression_fields: fields to retrieve
            @type expression_fields: <key:string,value:string> dict with
                          key in 
                          { "ResourceID", "DateModified", "DisplayName",
                          "DisplayNameLastModified", "PersonalStatus", 
                          "PersonalStatuslastModified", 
                          "StaticUserTilePublicURL",
                          "Photo", "Flags" }
                          and value in {"true", "false"}
        """
        self.__scenario = scenario
        self._method("GetProfile", callback, *callback_args, {})
        profileHandle = self.request.add_argument("profileHandle")
        Alias = profileHandle.append("Alias")
        Alias.append("Name", value=cid)
        Alias.append("NameSpace", value="MyCidStuff")
        profileHandle.append("RelationshipName", value="MyProfile")
        profileAttributes = self.request.add_argument("profileAttributes")
        for field, retrieve in fields.iteritems():
            profileAttributes.append(field, value=retrieve)
        ExpressionProfileAttributes = profileAttributes.append("ExpressionProfileAttributes")
        for field, retrieve in expression_fields.iteritems():
            ExpressionProfileAttributes.append(field, retrieve)
        self.send_request()

    def UpdateProfile(self, scenario, rid, fields,
                      callback, *callback_args):
        """call the UpdateProfile SOAP action

            @param scenario: the scenario to use for the action
            @type scenario: string in {"RoamingIdentityChanged"}

            @param rid: resource id
            @type rid: string

            @param fields: fields to update
            @type fields: <key:string,value:string> dict with
                          key in {"DisplayName", "PersonalStatus"}
        """
        self.__scenario = scenario
        self._method("UpdateProfile", callback, *callback_args, {})
        profile = self.request.add_argument("profile")
        profile.append("ResourceID", value=rid)
        ExpressionProfile = profile.append("ExpressionProfile")
        ExpressionProfile.append("FreeText", value="Update")
        for field, nvalue in fields.iteritems():
            ExpressionProfile.append(field, value=nvalue)
        ExpressionProfile.append("Flags", value="0")
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
        Relationship = self.request.add_argument("relationships").\
            append("Relationship")
        Relationship.append("SourceID", value=sourceid)
        Relationship.append("SourceType", value=sourcetype)
        Relationship.append("TargetID", value=targetid)
        Relationship.append("TargetType", value=targettype)
        Relationship.append("RelationshipName", value=relationship)
        self.send_request()


    def DeleteRelationships(self, scenario, relationship, cid, rid
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
        sourceHandle = self.request.add_argument("sourceHandle")
        sourceHandle.append("RelationshipName", relationship)
        Alias = sourceHandle.append("Alias")
        Alias.append("Name", cid)
        Alias.append("NameSpace", "MyCidStuff")
        targetHandles = self.request.add_argument("targetHandles")
        targetHandles.append("ObjectHandle").\
            append("ResourceID", value=rid)
        self.send_request()

    def CreateDocument(self, scenario, 
                       callback, *callback_args):
        self.__scenario = scenario
        pass

    def FindDocument(self, scenario, 
                     callback, *callback_args):
        self.__scenario = scenario
        pass

    def _extract_response(self, method, soap_response):
        if method == "GetProfile":
            pass
        else:
            return SOAPService._extract_response(self, method, soap_response)
