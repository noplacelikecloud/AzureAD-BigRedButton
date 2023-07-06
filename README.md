# Azure AD Glass Break CLI Application

This Command-Line Interface (CLI) application provides glass break access to Azure AD (Active Directory) in case of an emergency using a service principal. It allows users to perform various tasks related to setting up, managing, and revoking glass break access in Azure AD. The application interacts with Azure AD through the Azure AD Graph API and utilizes the Azure Identity library for authentication.

## Features

The Azure AD Glass Break CLI Application provides the following features:

- **New Glass Break Access Setup**: Set up a new glass break access by creating a service principal, assigning permissions, and exporting the service principal credentials to a JSON file.
- **Emergency Access Provisioning**: Provide emergency access to Azure AD by creating a user account, assigning the user account to an Azure AD role, and disabling Conditional Access policies.
- **Conditional Access Disabling**: Disable Conditional Access policies in Azure AD.
- **Glass Break Access Removal**: Remove the glass break access by deleting the service principal and optionally invalidating the credentials file.
- **Validation of Credentials**: Validate the credentials in the credentials file.
- **Automated Tasks**: Perform tasks automatically by passing command-line arguments to the CLI application.

## Prerequisites

To run this application, make sure you have the following prerequisites:

- Python 3.x installed on your system.
- Azure AD tenant with appropriate permissions to create and manage service principals, users, and Conditional Access policies.
- Azure AD Graph API permissions and client secret associated with the Azure AD tenant.
- Azure Identity library installed (`pip install azure-identity`).

## Getting Started

1. Clone this repository to your local machine.
2. Install the required dependencies by running the following command:
   ```
   pip install -r requirements.txt
   ```
3. Provide the necessary configurations and credentials:
   - Configure the Azure AD Graph API permissions and client secret by following the setup instructions provided.
   - Create a `credentials.json` file with the necessary credentials (see the example file provided).
4. Run the `main.py` script to start the CLI application:
   ```
   python main.py
   ```
   - You can also run automated tasks by passing command-line arguments. For example:
     - To test the glass break access:
       ```
       python main.py -t
       ```
     - To renew the service principal token:
       ```
       python main.py -r
       ```
     - To perform other tasks, use the appropriate command-line arguments as needed.
5. Follow the on-screen instructions or command-line arguments to navigate through the application and perform the desired actions.

## Usage

The Azure AD Glass Break CLI Application provides a menu-driven interface to choose different tasks. Follow the instructions provided by the application to select an option and provide the required information.

Alternatively, you can run the application with the following command-line arguments:

- `-t` or `--test`: Test the glass break access.
- `-r` or `--renew`: Renew the service principal token.
- `-f` or `--credentials-file`: Path to the credentials file.

For example, to test the glass break access automatically without user interaction, run the following command:
```
python main.py -t -f <path_to_credentials_file>
```

Note: Please exercise caution while using the glass break access functionality as it provides emergency access to your Azure AD environment. Ensure that you have a clear understanding of the implications and security considerations.

## Additional Resources

- [Azure AD Graph API documentation](https://docs.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0)
- [Azure Identity library documentation](https://docs.microsoft.com/en-us/python/api/azure-identity/?view=azure-python)

## License

This project is licensed under the [MIT License](LICENSE).

Feel free to customize this `README.md` file according to your project's specific details and requirements.