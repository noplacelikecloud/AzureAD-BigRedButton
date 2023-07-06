import azure.identity as azid
import os
import json

class ServicePrincipal:

    def __init__(self, SpObjectId : str = "", clientSecret : str = "", tenantId : str = "", applicationId : str = "", objectId : str = "", secretId = "") -> None:
        self.SpObjectId = SpObjectId
        self.clientSecret = clientSecret
        self.tenantId = tenantId
        self.applicationId = applicationId
        self.objectId = objectId
        self.secretId = secretId
    
    def test(self) -> bool:
        creds = azid.ClientSecretCredential(tenant_id=self.tenantId, client_id=self.applicationId, client_secret=self.clientSecret)
        try:
            token = creds.get_token("https://graph.microsoft.com/.default").token
        except:
            return False
        
        return True

class UserObj:
    
    def __init__ (self, userId : str = "", upn : str = "", password : str = ""):
        self.userId = userId
        self.upn = upn
        self.password = password

class StateModel:

    def __init__ (self, EmergencyAccessActive = False, EA_UserId = "", policy_ids= ""):
        # Check if Statefile is present
        if os.path.isfile("state.json"):
            # Read Statefile
            with open("state.json", "r") as statefile:
                state = json.load(statefile)
                statefile.close()
            # Parse Statefile
            self.EmergencyAccessActive = state["EmergencyAccessActive"]
            self.EA_UserId = state["EA_UserId"]
            self.policy_ids = state["policy_ids"]
        else:
            self.EmergencyAccessActive = EmergencyAccessActive
            self.EA_UserId = EA_UserId
            self.policy_ids = policy_ids
        