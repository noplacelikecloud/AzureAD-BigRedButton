import requests
import json
from models import UserObj, ServicePrincipal
import time
import os
import qrcode
import jinja2
import pdfkit
import datetime

import password_generator as pg

def GetTenantId(token:str) -> str:
    # Module for getting tenant id
    print("Get tenant id")
    response = REST_API("https://graph.microsoft.com/v1.0/organization", token, None, "GET")

    if response.status_code == 200:
        print("Tenant id found")
        return response.json()['value'][0]['id']
    elif response.status_code == 401:
        print("Unauthorized")
        return None
    elif response.status_code == 403:
        print("Forbidden")
        return None
    elif response.status_code == 404:
        print("Not found")
        return None
    elif response.status_code == 500:
        print("Internal server error")
        return None
    else:
        print("Unknown error")
        print(response.text)
        return None

def GetUPN(token:str) -> str:
    # Module for getting tenant id
    print("Get tenant id")
    response = REST_API("https://graph.microsoft.com/v1.0/organization", token, None, "GET")

    if response.status_code == 200:
        print("Tenant id found")
        return response.json()['value'][0]['verifiedDomains'][0]['name']
    elif response.status_code == 401:
        print("Unauthorized")
        return None
    elif response.status_code == 403:
        print("Forbidden")
        return None
    elif response.status_code == 404:
        print("Not found")
        return None
    elif response.status_code == 500:
        print("Internal server error")
        return None
    else:
        print("Unknown error")
        print(response.text)
        return None

def REST_API(url:str, token:str, body:object, method:str):
    # Module for REST API
    # Create request

    # Set headers
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Send request
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=body)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=body)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        print("Invalid method")
        return None
    
    if response.status_code != 200 and response.status_code != 201 and response.status_code != 204:
        print("Error: " + str(response.status_code))
        print(response.text)
    
    response.encoding = 'utf-8'
    return response

def CreateServicePrincipal(name:str, token:str) -> (bool, ServicePrincipal):
    #Module for creating SP with API permission Policy.ReadWrite.ConditionalAccess
    #Init SP Object
    ServPrinc = ServicePrincipal()
    # Check if SP already exists
    print("Check if SP already exists")
    response = REST_API("https://graph.microsoft.com/v1.0/servicePrincipals?$filter=displayName eq '" + name + "'", token, None, "GET")
    if response.json()['value'] != []:
        # Inform user that SP already exists and ask if he wants to continue
        print("Emergency access already exists! \n Creating further SPs will not change your existing access. Be informed that having multiple SPs increases your attack surface to attackers. \n")
        while True:
            choice = input("Do you want to continue?  (y/n) ")
            if choice == "y":
                break
            elif choice == "n":
                exit(0)
        
    print("Create App registration")
    response_app = REST_API("https://graph.microsoft.com/v1.0/applications", token, {"displayName": name}, "POST")

    if response_app.status_code == 201:
        ServPrinc.applicationId = response_app.json()['appId']
        ServPrinc.SpObjectId = response_app.json()['id']
        # Create SP from App registration
        print("Create SP from App registration")
        response_SP = REST_API("https://graph.microsoft.com/v1.0/servicePrincipals/", token, {"appId":  ServPrinc.applicationId}, "POST")
        if response_SP.status_code == 201:
            print("SP created")
            ServPrinc.objectId = response_SP.json()['id']
            # Add secret
            url = f'https://graph.microsoft.com/v1.0/applications/{ServPrinc.SpObjectId}/addPassword'
            response_secret = REST_API(url, token, None, "POST")
            if response_secret.status_code == 200:
                print("Secret created")
                ServPrinc.secretId = response_secret.json()['keyId']
                ServPrinc.clientSecret = response_secret.json()['secretText']
                EndOfValidity = response_secret.json()['endDateTime']
                EndOfValidity = datetime.datetime.strptime(EndOfValidity[:26], '%Y-%m-%dT%H:%M:%S.%f')
                ServPrinc.secretValidUntil = EndOfValidity.strftime('%d.%m.%Y %H:%M:%S'+ " UTC")
            else:
                print("Error creating secret")
                print(response_secret.text)
                return False, None
            return True, ServPrinc
        else:
            print("Error creating SP")
            print(response_SP.text)
            return False, None
    elif response.status_code == 400:
        print("Bad request")
        return False, None
    elif response.status_code == 401:
        print("Unauthorized")
        return False, None
    elif response.status_code == 403:
        print("Forbidden")
        return False, None
    elif response.status_code == 404:
        print("Not found")
        return False, None
    elif response.status_code == 500:
        print("Internal server error")
        return False, None
    else:
        print("Unknown error")
        print(response_app.text)
        return False, None

def AssignPermissions(id:str, token:str):
    # Module for assigning global admin role to SP
    print("Assign Global Admin role to SP")

    # Add to Global Admin Role
    url = "https://graph.microsoft.com/v1.0/directoryRoles/roleTemplateId=62e90394-69f5-4237-9190-012177145e10/members/$ref"
    odata = "https://graph.microsoft.com/v1.0/directoryObjects/" + id
    response_assign = REST_API(url, token, {"@odata.id" : odata}, "POST")

    if response_assign.status_code == 204:
        print("Global Admin role assigned")
        # Add API permission
        print("Add API permission")
        url = f'https://graph.microsoft.com/v1.0/servicePrincipals/{id}/appRoleAssignments'
        body = {
        "principalId": id,
        "resourceId": "5e446bad-f814-4c29-918e-b7de3c56fa71", # Id of Microsoft Graph Application
        "appRoleId": "01c0a623-fc9b-48e9-b794-0756f8e8f067" # Id of Policy.ReadWrite.ConditionalAccess
        }
        response_permission = REST_API(url, token, body, "POST")

        if response_permission.status_code == 201:
            print("API permission added")
            return True
        else:
            print("Error adding API permission")
            print(response_permission.text)
            return False
    elif response_assign.status_code == 401:
        print("Unauthorized. Check if your account is a Global Admin")
        return False
    elif response_assign.status_code == 403:
        print("Forbidden")
        return False
    elif response_assign.status_code == 404:
        print("Not found")
        return False
    elif response_assign.status_code == 500:
        print("Internal server error")
        return False
    else:
        print("Unknown error")
        return False
    
def ExportCredentials(sp:ServicePrincipal, token: str, path:str = ".") -> bool:
    # create JSON file with tenantId, clientId and clientSecret
    sp.tenantId = GetTenantId(token)
    data = {
        "application_ObjectId": sp.SpObjectId,
        "secretId" : sp.secretId,
        "tenantId": sp.tenantId,
        "clientId": sp.applicationId,
        "clientSecret": sp.clientSecret,
        "ServicePrincipal_ObjectId": sp.objectId,
        "secretValidUntil": sp.secretValidUntil
    }
    try:
        with open(path + '/' + "credentials.json", "w") as outfile:
            json.dump(data, outfile)
            print("Credentials exported to credentials.json")
    except:
        print("Error writing to file, check if you have permissions to write to file")

    return True
    

def ReadCredentials(path : str) -> ServicePrincipal:

    spObj = ServicePrincipal()
    # Read JSON file
    with open(path, "r") as infile:
        jsonstr = infile.read().encode('utf-8')
        data = json.loads(jsonstr)

    # Check if JSON contains tenantId, clientId and clientSecret
    if 'tenantId' not in data or 'clientId' not in data or 'clientSecret' not in data:
        print("Invalid JSON file. Please check path and file.")
        exit(0)

    spObj.tenantId = data['tenantId']
    spObj.applicationId = data['clientId']
    spObj.clientSecret = data['clientSecret']
    spObj.objectId = data['ServicePrincipal_ObjectId']
    spObj.SpObjectId = data['application_ObjectId']
    spObj.secretId = data['secretId']
    spObj.secretValidUntil = data['secretValidUntil']

    return spObj

def CreateUser(token:str, username:str = None) -> (bool, UserObj):
    user = UserObj()
    # Create user
    if username is None:
        user.upn = input("Enter desired userPrincipalName (e.g. emergency@contoso.com): ")
    else:
        user.upn = username
    
    user.password = pg.generate(count=1, length=16)

    # Call REST API
    response = REST_API("https://graph.microsoft.com/v1.0/users", token, {"accountEnabled": True, "displayName": "Emergency Access", "mailNickname": "emergency", "userPrincipalName": user.upn, "passwordProfile": {"forceChangePasswordNextSignIn": False, "password": user.password}}, "POST")

    if response.status_code == 201:
        print("User created")
        user.userId = response.json()['id']
        return True, user
    elif response.status_code == 400:
        print("Bad request")
        return False, None
    elif response.status_code == 401:
        print("Unauthorized")
        return False, None
    elif response.status_code == 403:
        print("Forbidden")
        return False, None
    elif response.status_code == 404:
        print("Not found")
        return False, None
    elif response.status_code == 500:
        print("Internal server error")
        return False, None
    else:
        print("Unknown error")
        return False, None

def AssignUserPermissions(id:str, token:str):
    print(id)
    # Module for assigning global admin role to SP
    print("Assign Global Admin role to SP")

    # Add to Global Admin Role
    url = "https://graph.microsoft.com/v1.0/directoryRoles/roleTemplateId=62e90394-69f5-4237-9190-012177145e10/members/$ref"
    odata = f"https://graph.microsoft.com/v1.0/directoryObjects/{id}"
    response_assign = REST_API(url, token, {"@odata.id" : odata}, "POST")

    if response_assign.status_code == 204:
        print("Global Admin role assigned")
        return True
    elif response_assign.status_code == 401:
        print("Unauthorized. Check if your account is a Global Admin")
        return False
    elif response_assign.status_code == 403:
        print("Forbidden")
        return False
    elif response_assign.status_code == 404:
        print("Not found")
        return False
    elif response_assign.status_code == 500:
        print("Internal server error")
        return False
    else:
        print("Unknown error")
        print(response_assign.text)
        return False

def ToggleConditionalAccess(operation: str,token:str) -> (bool,[str]):
    if operation == "disable":
        list_policy_id = []
        # Disable Conditional Access
        print("Disable Conditional Access")
        url = "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies"
        response = REST_API(url, token, None, "GET")

        if response.status_code == 200:
            if len(response.json()['value']) == 0:
                print("No Conditional Access policies found")
                return True, None
            print("Conditional Access policies found")
            policies = response.json()['value']
            for policy in policies:
                if policy['state'] == 'enabled':
                    policyId = policy['id']
                    url = f"https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies/{policyId}"
                    response = REST_API(url, token, {"state": "disabled"}, "PATCH")
                    if response.status_code == 204:
                        print("Conditional Access policy disabled")
                        list_policy_id.append(policyId)
                    else:
                        print("Error disabling Conditional Access policy")
                        print(response.text)
                        return False, list_policy_id
            return True, list_policy_id
        elif response.status_code == 401:
            print("Unauthorized. Check if your account is a Global Admin")
            return False, None
        elif response.status_code == 403:
            print("Forbidden")
            return False, None
        elif response.status_code == 404:
            print("Not found")
            return False, None
        elif response.status_code == 500:
            print("Internal server error")
            return False, None
        else:
            print("Unknown error")
            print(response.text)
            return False, None
    
    elif operation == "enable":
        # Get list of previous active policies from state.json
        with open('state.json', "r") as infile:
            jsonstr = infile.read().encode('utf-8')
            data = json.loads(jsonstr)

        # Get id of previous active policies
        list_policy_id = data['policy_ids']

        # Enable Conditional Access
        print("Enable Conditional Access")
        for policyId in list_policy_id:
            url = f"https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies/{policyId}"
            response = REST_API(url, token, {"state": "enabled"}, "PATCH")
            if response.status_code == 204:
                print("Conditional Access policy enabled")
            else:
                print("Error enabling Conditional Access policy")
                print(response.text)
                return False, None
        return True, None

def DeleteServicePrincipal(sp: ServicePrincipal, token:str):
    # Delete Service Principal
    print("Delete Service Principal: " + sp.objectId)
    url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp.objectId}"
    response = REST_API(url, token, None, "DELETE")

    if response.status_code == 204:
        print(f"Service Principal {sp.objectId} deleted")
        return True
    elif response.status_code == 401:
        print("Unauthorized. Check if your account is a Global Admin")
        return False
    elif response.status_code == 403:
        print("Forbidden")
        return False
    elif response.status_code == 404:
        print("Not found")
        return False
    elif response.status_code == 500:
        print("Internal server error")
        return False
    else:
        print("Unknown error")
        print(response.text)
        return False
    
def GetServicePrincipals(token:str) -> (bool, [ServicePrincipal]):
    list_sp = []
    # Get all Service Principal with name "azure-ad-glass-break"
    print("Get Service Principals")
    url = "https://graph.microsoft.com/v1.0/servicePrincipals?$filter=displayName eq 'azure-ad-glass-break'"
    response = REST_API(url, token, None, "GET")

    if response.status_code == 200:
        # Iterate and delete them all
        print("Service Principals found")
        sps = response.json()['value']
        for sp in sps:
            # Create SP Object
            spObj = ServicePrincipal()
            spObj.objectId = sp['id']
            spObj.applicationId = sp['appId']
            list_sp.append(spObj)
        
        return True, list_sp

    elif response.status_code == 401:
        print("Unauthorized. Check if your account is a Global Admin")
        return False, None
    elif response.status_code == 403:
        print("Forbidden")
        return False, None
    elif response.status_code == 404:
        print("Not found")
        return False, None
    elif response.status_code == 500:
        print("Internal server error")
        return False, None
    else:
        print("Unknown error")
        print(response.text)
        return False, None

def DeleteAppRegistration(spObj:ServicePrincipal, token:str) -> bool:
    # Delete App Registration
    print("Delete App Registration")
    url = f"https://graph.microsoft.com/v1.0/applications(appId='{spObj.applicationId}')"
    response = REST_API(url, token, None, "DELETE")

    if response.status_code == 204:
        print("App Registration deleted")
        return True
    elif response.status_code == 401:
        print("Unauthorized. Check if your account is a Global Admin")
        return False
    elif response.status_code == 403:
        print("Forbidden")
        return False
    elif response.status_code == 404:
        print("Not found")
        return False
    elif response.status_code == 500:
        print("Internal server error")
        return False
    else:
        print("Unknown error")
        print(response.text)
        return False

def WriteStateFile(user = None, policyIds = None, EmergencyAccessActive = None) -> bool:
    # Check if state file is present
    if os.path.isfile('state.json'):
        # Read state file
        with open('state.json', "r") as infile:
            jsonstr = infile.read().encode('utf-8')
            data = json.loads(jsonstr)

            # Change all non null values
            if user is not None:
                data['objectId'] = user.userId
            if policyIds is not None:
                data['policy_id'] = policyIds
            if EmergencyAccessActive is not None:
                data['EmergencyAccessActive'] = EmergencyAccessActive
            
            # Write state file
            try:
                with open('state.json', 'w') as outfile:
                    json.dump(data, outfile)
            except:
                print("Error writing state file")
                return False
            
            return True
    else:
        # Create state file
        print("Create state file")
        # Change all null values to []
        if user is None:
            user = UserObj()
            user.userId = ""
        if policyIds is None:
            policyIds = []
        if EmergencyAccessActive is None:
            EmergencyAccessActive = False

        state = {
            "EmergencyAccessActive" : EmergencyAccessActive,
            "EA_UserId": user.userId,
            "policy_ids": policyIds
        }
        try:
            with open('state.json', 'w') as outfile:
                json.dump(state, outfile)
        except:
            print("Error creating state file")
            return False
        
        return True

def DeleteEmergencyUser(token:str):
    # Get user id from state.json
    with open('state.json', "r") as infile:
        jsonstr = infile.read().encode('utf-8')
        data = json.loads(jsonstr)

    # Get id of previous active policies
    userId = data['EA_UserId']

    # Check if user id is not empty
    if userId != "":
        # Delete user
        print("Delete Emergency User")
        url = f"https://graph.microsoft.com/v1.0/users/{userId}"
        response = REST_API(url, token, None, "DELETE")

        if response.status_code == 204:
            print("Emergency User deleted")
            return True
        elif response.status_code == 401:
            print("Unauthorized. Check if your account is a Global Admin")
            return False
        elif response.status_code == 403:
            print("Forbidden")
            return False
        elif response.status_code == 404:
            print("Not found")
            return False
        elif response.status_code == 500:
            print("Internal server error")
            return False
        else:
            print("Unknown error")
            print(response.text)
            return False
    else:
        print("No Emergency User found")
        input("Please confirm you deleted the user manually. If not, please do so now.")
        return True

def RenewSecret(token:str, creds:ServicePrincipal) -> (bool, ServicePrincipal):
    # Delete old secret
    print("Delete old secret")
    url = f"https://graph.microsoft.com/v1.0/applications/{creds.SpObjectId}/removePassword"
    body = {
        "keyId": creds.secretId
    }
    response = REST_API(url, token, body, "POST")

    if response.status_code == 204:
        print("Secret deleted")
        # Create new secret
        print("Create new secret")
        url = f"https://graph.microsoft.com/v1.0/applications/{creds.SpObjectId}/addPassword"
        response = REST_API(url, token, None, "POST")

        if response.status_code == 200:
            print("Secret created")
            creds.secretId = response.json()['keyId']
            creds.clientSecret = response.json()['secretText']
            EndOfValidity = response.json()['endDateTime']
            EndOfValidity = datetime.datetime.strptime(EndOfValidity[:26], '%Y-%m-%dT%H:%M:%S.%f')
            creds.secretValidUntil = EndOfValidity.strftime('%d.%m.%Y %H:%M:%S'+ " UTC")
            return True, creds
        elif response.status_code == 401:
            print("Unauthorized. Check if your account is a Global Admin")
            return False,None
        elif response.status_code == 403:
            print("Forbidden")
            return False,None
        elif response.status_code == 404:
            print("Not found")
            return False,None
        elif response.status_code == 500:
            print("Internal server error")
            return False,None
        else:
            print("Unknown error")
            print(response.text)
            return False,None
    elif response.status_code == 401:
        print("Unauthorized. Check if your account is a Global Admin")
        return False,None
    elif response.status_code == 403:
        print("Forbidden")
        return False,None
    elif response.status_code == 404:
        print("Not found")
        return False,None
    elif response.status_code == 500:
        print("Internal server error")
        return False,None
    else:
        print("Unknown error")
        print(response.text)
        return False,None

def ExportVaultPDF(sp: ServicePrincipal, path: str) -> bool:
    try:
        # Generate QR Code with credentials file
        print("Generate QR Code with credentials file")
        qr = qrcode.QRCode()

        # build json string
        jsonstr = json.dumps(sp.__dict__)
        qr.add_data(jsonstr)

        # create qr code as png
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("qr.png")

        # Set variables for template
        context = {}
        context['domain'] = sp.getDomain()
        context['tenantId'] = sp.tenantId
        context['clientId'] = sp.applicationId
        context['clientSecret'] = sp.clientSecret
        context['QRCode'] = os.path.dirname(os.path.abspath(__file__)) + "/qr.png"
        context['CSSFile'] = os.path.dirname(os.path.abspath(__file__)) + "/templates/style.css"
        context['validUntil'] = sp.secretValidUntil

        # Generate PDF with QR Code
        print("Generate PDF with QR Code")
        template_loader = jinja2.FileSystemLoader(searchpath="./")
        template_env = jinja2.Environment(loader=template_loader)

        template = template_env.get_template("templates/pdf_template.html")
        outputText = template.render(context)

        path = path + "BreakGlassInformation.pdf"

        pdfkit.from_string(outputText, path, options={"enable-local-file-access": ""})

        print("Vault PDF generated")

        return True

    except Exception as e:
        print("Error generating PDF")
        print(e)
        return False
    