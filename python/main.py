# CLI Application for providing glass break access to Azure AD in case of emergency using service principal
#
# Author: Bernhard Flür
# Date: 2023-07-05
# Version: 0.1

import os
import sys, argparse
import json
import logging
import argparse
import requests
import azure.identity as azid
import string, random

from helper import *
from models import *

firstMenuChoice = None

def welcome():
    print("\n###############################################")
    print("Welcome to the Azure AD Glass Break CLI Application")
    print("This application is used to provide access to Azure AD in case of emergency")
    print("Please provide the required information to get started")
    print("############################################### \n")

def StartMenu():

    # Choose if you want to set up a new glass break access or if you want to use an existing one
    print("Please choose if you want to set up a new glass break access or if you want to use an existing one \n \n")
    print("###############################################")
    print("########## ADMINISTRATIVE TASKS ###############")
    print("############################################### \n")
    print("1. Set up a new glass break access")
    print("2. Delete glass break access")
    print("3. Validate credentials")
    print("4. Renew secret key")
    print("5. Generate Vault PDF \n")

    print("###############################################")
    print("########## EMERGENCY TASKS ####################")
    print("############################################### \n")
    print("6. Provide emergency access")
    print("7. Disable Conditional Access\n")

    print("###############################################")
    print("########## RECOVERY TASKS #####################")
    print("############################################### \n")
    print("8. Rollback emergency access/conditional access\n")

    print("9. Exit \n")
    choice = input("Please enter your choice: ")

    return choice

def CreateNewGlassBreakAccess():
    # Authenticate to Azure AD using interactive login
    print("Please authenticate to Azure AD using interactive login")
    creds = azid.InteractiveBrowserCredential()
    if not creds:
        print("Authentication failed")
        sys.exit(1)

    # Get path for credentials file
    while True:
        print("Please provide the path for the credentials file")
        path = input("Please enter the path: ")

        # Check if path exists
        if not os.path.exists(path):
            print("Path does not exist")
            continue
        
        break

    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]
    
    # Create new service principal
    token = creds.get_token('https://graph.microsoft.com/.default').token
    spName = 'azure-ad-glass-break'
    success, ServPrinc = CreateServicePrincipal(spName, token)

    if not success:
        print("Service principal creation failed")
        sys.exit(1)
    
    # Assign permissions to service principal (Global Admin)
    print("Assigning permissions to service principal")
    permissions = AssignPermissions(ServPrinc.objectId, token)

    if not permissions:
        print("Assigning permissions failed")
        sys.exit(1)
    
    # Export service principal credentials to JSON file
    print("Exporting service principal credentials to JSON file")
    export = ExportCredentials(ServPrinc, token, path)

    if not export:
        print("Exporting credentials failed")
        sys.exit(1)
    
    print("Waiting for secret to be available - 30 seconds")
    #Sleep to make sure that secret is available
    i = 0
    while i < 30:
        print(".", end="", flush=True)
        time.sleep(1)
        i += 1

    # Test credentials
    if ServPrinc.test():
        print("Credentials are valid")
    else:
        print("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Create PDF file
    print("Creating PDF file")
    success = ExportVaultPDF(ServPrinc, ".")

    if not success:
        print("Creating PDF file failed")
        sys.exit(1)
    
    print("PDF file created successfully")
    
    print("Glass break access successfully created!")
    print("Please store the credentials file + pdf on a safe place!")
    print("Your credentials are vaild until " + ServPrinc.secretValidUntil)
    print("Please make sure to renew your credentials before they expire. For this, you can use the renew secret key function")

def ProvideEmergencyAccess():
    # Provide path of the credentials file
    print("Please provide the path of the credentials file")
    while True:
        path = input("Please enter the path: [Default: ./credentials.json] ")

        if path == "":
            path = "./credentials.json"

        # Check if path exists
        if not os.path.exists(path):
            print("Path does not exist")
            continue
        
        break
    
    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]
    
    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    if credentials.test():
        print("Credentials are valid")
    else:
        print("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Authenticate to Azure AD using service principal
    token = azid.ClientSecretCredential(tenant_id=credentials.tenantId, client_id=credentials.applicationId, client_secret=credentials.clientSecret).get_token('https://graph.microsoft.com/.default').token
    
    # Create user account
    print("Creating user account")
    success_user, user = CreateUser(token)

    if not success_user:
        print("Creating user account failed")
        sys.exit(1)
    
    time.sleep(10)

    # Assign user account to Azure AD role
    print("Assigning user account to Azure AD role")
    success_role = AssignUserPermissions(user.userId, token)

    if not success_role:
        print("Assigning user account to Azure AD role failed")
        sys.exit(1)

    # Disable Conditional Access
    print("Disabling Conditional Access")
    success_ca, PolicyIds = ToggleConditionalAccess(token=token, operation="disable")

    if not success_ca:
        print("Disabling Conditional Access failed")
        sys.exit(1)
    
    if PolicyIds == None:
        print("No Conditional Access Policies found")
    
    # create state file to detect active glass break access
    success_state = WriteStateFile(user=user, EmergencyAccessActive=True, policyIds=PolicyIds)
    
    print("Emergency account successfully created")
    print("Conditional Access Policies disabled \n \n")
    print("Sign in using following credentials: ")
    print("Username: " + user.upn)
    print("Password: " + user.password)


def DisableCA():
    # Provide path of the credentials file
    print("Please provide the path of the credentials file")
    while True:
        path = input("Please enter the path: [Default: ./credentials.json] ")

        if path == "":
            path = "./credentials.json"

        # Check if path exists
        if not os.path.exists(path):
            print("Path does not exist")
            continue
        
        break
    
    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]
    
    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    if credentials.test():
        print("Credentials are valid")
    else:
        print("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Authenticate to Azure AD using service principal
    token = azid.ClientSecretCredential(tenant_id=credentials.tenantId, client_id=credentials.applicationId, client_secret=credentials.clientSecret).get_token("https://graph.microsoft.com/.default").token
    
    # Disable CA
    print("Disabling CA")
    success, PolicyIds = ToggleConditionalAccess(token=token, operation="disable")

    if not success:
        print("Disabling CA failed")
        sys.exit(1)
    
    if PolicyIds == None:
        print("No Conditional Access policies found.")
        sys.exit(0)

    success_SF = WriteStateFile(user=None, EmergencyAccessActive=False, policyIds=PolicyIds)

    if not success_SF:
        print("Writing state file failed")
        print("State of CA Policies are unknown. Please reenable CA manually")

    
    print("CA successfully disabled")

def RemoveGlassBreakAccess():
    # Inform admin about consecuences
    print("WARNING!! Removing glass break access will delete the service principal and leads to invalidating the credentials file. There is no more access to the tenant using the glass break SP!")
    while True:
        print("Do you want to continue? [y/n]")
        choice = input("Please enter your choice: ")

        if choice == "y":
            break
        elif choice == "n":
            sys.exit(1)
        else:
            print("Invalid input")
            continue

    # Ask if credentials file is available. If not, all SP with name "azure-ad-glass-break" will be deleted
    while True:
        print("Do you have the credentials file? [y/n]")
        choice = input("Please enter your choice: ")

        if choice == "y":
            # Get path for credentials file
            while True:
                print("Please provide the path for the credentials file")
                path = input("Please enter the path: ")

                # Check if path exists
                if not os.path.exists(path):
                    print("Path does not exist")
                    continue

                # make sure there is no / at end of string
                if path[-1] == "/":
                    path = path[:-1]
                
                break
            break

        elif choice == "n":
            path = None
            print("All service principals with name 'azure-ad-glass-break' will be deleted. Is this ok? [y/n]")
            while True:
                choice = input("Please enter your choice: ")

                if choice == "y":
                    break
                elif choice == "n":
                    sys.exit(1)
                else:
                    print("Invalid input")
                    continue
            break
        else:
            print("Invalid input")
            continue
    
    if path != None:
            
        # Read credentials from JSON file
        print("Reading credentials from JSON file")
        credentials = ReadCredentials(path)

        if credentials.test():
            print("Credentials are valid")
        else:
            print("Credentials are invalid. Check your credentials file")
            sys.exit(1)
        
        # Authenticate to Azure AD using interactive login
        print("Authenticating to Azure AD using interactive login")
        token = azid.InteractiveBrowserCredential().get_token("https://graph.microsoft.com/.default").token

        # Delete service principal from Azure AD
        print("Deleting service principal from Azure AD")
        success_sp = DeleteServicePrincipal(credentials, token)
        sucess_app = DeleteAppRegistration(credentials, token)

        if not success_sp or not sucess_app:
            print("Deleting service principal failed")
            sys.exit(1)
        
        print("Service principal successfully deleted")
    
    else:
        credentials = None
        # Authenticate to Azure AD using interactive login
        print("Authenticating to Azure AD using interactive login")
        token = azid.InteractiveBrowserCredential().get_token("https://graph.microsoft.com/.default").token

        # Get all service principals with name "azure-ad-glass-break"
        print("Getting all service principals with name 'azure-ad-glass-break'")
        success, servicePrincipals = GetServicePrincipals(token)

        if not success:
            print("Getting service principals failed")
            sys.exit(1)

        
        if servicePrincipals == []:
            print("No glass break service principals found")
            sys.exit(1)
        
        # Delete all service principals
        print("Deleting all service principals")
        for servicePrincipal in servicePrincipals:
            success_sp = DeleteServicePrincipal(servicePrincipal, token)
            success_app = DeleteAppRegistration(servicePrincipal, token)

            if not success_sp or not success_app:
                print("Deleting service principal failed")
                sys.exit(1)
        
        # Delete credentials file
        print("Deleting credentials file")
        os.remove("./credentials.json")
        
        print("All service principals successfully deleted")

def RollbackEmergencyAccess(isAutomated:bool = False, autoPath:str = None):

    if not isAutomated:
        # Provide path of the credentials file
        print("Please provide the path of the credentials file")
        while True:
            path = input("Please enter the path: [Default: ./credentials.json] ")

            if path == "":
                path = "./credentials.json"

            # Check if path exists
            if not os.path.exists(path):
                print("Path does not exist")
                continue
            
            break

        # make sure there is no / at end of string
        if path[-1] == "/":
            path = path[:-1]
    else:
        path = autoPath
    
    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    if credentials.test():
        print("Credentials are valid")
    else:
        print("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Authenticate to Azure AD using service principal
    token = azid.ClientSecretCredential(tenant_id=credentials.tenantId, client_id=credentials.applicationId, client_secret=credentials.clientSecret).get_token("https://graph.microsoft.com/.default").token

    # Enable CA
    print("Enabling CA")
    success = ToggleConditionalAccess(operation="enable", token=token)

    if not success:
        print("Enabling CA failed")
        sys.exit(1)
    
    print("CA successfully enabled")

    # Delete emergency user if EmergencyActive Flag is True
    state = StateModel()
    if state.EmergencyAccessActive:
        # Delete emergency user
        print("Deleting emergency user")
        success = DeleteEmergencyUser(token)

        if not success:
            print("Deleting emergency user failed")
            sys.exit(1)
        
        print("Emergency user successfully deleted")
    else:
        print("No emergency user to delete")

    # Delete state file
    os.remove("./state.json")

    print("Rollback successfully completed")

def ValidateCreds() -> None:
    # Provide path of the credentials file
    print("Please provide the path of the credentials file")
    while True:
        path = input("Please enter the path: [Default: ./credentials.json] ")

        if path == "":
            path = "./credentials.json"

        # Check if path exists
        if not os.path.exists(path):
            print("Path does not exist")
            continue
        
        break

    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]

    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    # Validate credentials

    if credentials.test():
        print("Credentials are valid!")
    else:
        print("ERROR: Credentials are not valid! Please check credentials file and recover access")
    
    sys.exit()

def TestBreakGlassAccess(path: str) -> None:
    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]
    
    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    if credentials.test():
        print("Credentials are valid")
    else:
        raise Exception("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Authenticate to Azure AD using service principal
    token = azid.ClientSecretCredential(tenant_id=credentials.tenantId, client_id=credentials.applicationId, client_secret=credentials.clientSecret).get_token('https://graph.microsoft.com/.default').token
    
    letters = string.ascii_lowercase
    rand_username = ''.join(random.choice(letters) for i in range(8)) + '@' + GetUPN(token)

    print("Creating user account: " + rand_username)

    # Create user account
    print("Creating user account")
    success_user, user = CreateUser(token, rand_username)

    if not success_user:
        raise Exception("Creating user account failed")
        sys.exit(1)
    
    time.sleep(10)

    # Assign user account to Azure AD role
    print("Assigning user account to Azure AD role")
    success_role = AssignUserPermissions(user.userId, token)

    if not success_role:
        raise Exception("Assigning user account to Azure AD role failed")
        sys.exit(1)

    # Disable Conditional Access
    print("Disabling Conditional Access")
    success_ca, PolicyIds = ToggleConditionalAccess(token=token, operation="disable")

    if not success_ca:
        raise Exception("Disabling Conditional Access failed")
        sys.exit(1)
    
    if PolicyIds == None:
        print("No Conditional Access Policies found")
    
    # create state file to detect active glass break access
    success_state = WriteStateFile(user=user, EmergencyAccessActive=True, policyIds=PolicyIds)

    # Rollback emergency access test
    RollbackEmergencyAccess(autoPath=path, isAutomated=True)
    
def RenewSPSecret(isAutomated: bool = False, autoPath:str = None) -> None:
    if not isAutomated:
        # Provide path of the credentials file
        print("Please provide the path of the credentials file")
        while True:
            path = input("Please enter the path: [Default: ./credentials.json] ")

            if path == "":
                path = "./credentials.json"

            # Check if path exists
            if not os.path.exists(path):
                print("Path does not exist")
                continue
            
            break
    else:
        path = autoPath
    
    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]
    
    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    if credentials.test():
        print("Credentials are valid")
    else:
        print("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Authenticate to Azure AD using service principal
    token = azid.ClientSecretCredential(tenant_id=credentials.tenantId, client_id=credentials.applicationId, client_secret=credentials.clientSecret).get_token('https://graph.microsoft.com/.default').token

    # Renew SP secret
    print("Renewing SP secret")
    success, credentials = RenewSecret(token, credentials)

    # Write credentials to file
    print("Writing credentials to file")
    ExportCredentials(credentials, token)

    # Wait for 15 seconds to make sure the new secret is active
    print("Waiting for 30 seconds to make sure the new secret is active")
    i= 0
    while i <= 30:
        print(".", end="", flush=True)
        time.sleep(1)
        i += 1
        continue

    print("\n")

    # Create PDF file
    print("Creating PDF file")
    success = ExportVaultPDF(credentials, ".")

    if not success:
        print("Creating PDF file failed")
        sys.exit(1)
    
    print("PDF file created successfully")
    
    print("Successfully renewed SP secret")
    print("Please replace the new credentials file + pdf!")

def GeneratePDF() -> None:
    # Get path of the credentials file
    print("Please provide the path of the credentials file")
    while True:
        path = input("Please enter the path: [Default: ./credentials.json] ")

        if path == "":
            path = "./credentials.json"

        # Check if path exists
        if not os.path.exists(path):
            print("Path does not exist")
            continue
        
        break

    # make sure there is no / at end of string
    if path[-1] == "/":
        path = path[:-1]

    # Get path for PDF file
    print("Please provide the path of the PDF file")
    while True:
        path_pdf = input("Please enter the path: [Default: ./] ")

        if path_pdf == "":
            path_pdf = "./"

        # Check if path exists
        if not os.path.exists(path_pdf):
            print("Path does not exist")
            continue
        
        break

    # make sure there is no / at end of string
    if path_pdf[-1] == "/":
        path_pdf = path_pdf[:-1]

    # Read credentials from JSON file
    print("Reading credentials from JSON file")
    credentials = ReadCredentials(path)

    if credentials.test():
        print("Credentials are valid")
    else:
        print("Credentials are invalid. Check your credentials file")
        sys.exit(1)
    
    # Create PDF file
    print("Creating PDF file")
    success = ExportVaultPDF(credentials, path_pdf)

    if not success:
        print("Creating PDF file failed")
        sys.exit(1)
    
    print("PDF file created successfully")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="Test break glass access", action="store_true")
    parser.add_argument("-r", "--renew", help="Renew the SP Token", action="store_true")
    parser.add_argument("-f", "--credentials-file", help="Path of the credentials-file")

    cli_params = parser.parse_args()

    if cli_params.test:
        path = cli_params.credentials_file
        TestBreakGlassAccess(path)
        sys.exit()
    if cli_params.renew:
        path = cli_params.credentials_file
        RenewSPSecret(isAutomated=True, autoPath=path)
        sys.exit()
    welcome()
    menuChoice = StartMenu()

    if menuChoice == "1":
        CreateNewGlassBreakAccess()
    
    elif menuChoice == "2":
        RemoveGlassBreakAccess()

    elif menuChoice == "3":
        ValidateCreds()
    
    elif menuChoice == "4":
        RenewSPSecret()

    elif menuChoice == "5":
        GeneratePDF()
    
    elif menuChoice == "6":
        ProvideEmergencyAccess()

    elif menuChoice == "7":
        DisableCA()

    elif menuChoice == "8":
        RollbackEmergencyAccess()

if __name__ == "__main__":
    main()