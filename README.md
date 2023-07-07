# Glass Break Access - Code Project

This code project provides a CLI application for managing glass break access to Azure AD in case of emergencies. It allows you to set up a new glass break access, provide emergency access, disable conditional access, and perform other administrative and recovery tasks.

## Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/noplacelikecloud/AzureAD-BigRedButton.git
   ```

2. Change to the project directory:

   ```shell
   cd AzureAD-BigRedButton
   ```

3. Install the required dependencies:

   ```shell
   pip install -r requirements.txt
   ```

## Project Structure

The project repository has the following structure:

```
repo
├── README.md
├── python
│   ├── helper.py
│   ├── main.py
│   ├── models.py
│   └── templates
│       ├── pdf_template.html
│       └── style.css
├── requirements.txt
├── start.cmd
└── start.sh
```

- `README.md`: This file provides an overview of the project.
- `python`: This directory contains the Python source code files.
    - `helper.py`: This file contains helper functions used in the application.
    - `main.py`: This file is the main entry point of the CLI application.
    - `models.py`: This file defines the data models used in the application.
    - `templates`: This directory contains HTML and CSS templates for generating PDF reports.
        - `pdf_template.html`: This HTML template is used for generating PDF reports.
        - `style.css`: This CSS file contains styling for the PDF template.
- `requirements.txt`: This file lists the dependencies required by the project.
- `start.cmd`: This is a Windows command script for starting the application.
- `start.sh`: This is a Unix shell script for starting the application.

## Usage

To use the CLI application, follow these steps:

1. Run the application using one of the start scripts:
    - On Windows: Run `start.cmd`.
    - On Unix-based systems: Run `start.sh`.
2. Follow the prompts in the CLI to perform the desired tasks.

## Functionality

The CLI application provides the following functionality:

- **Set up a new glass break access**: This option allows you to authenticate to Azure AD, create a new service principal, assign permissions, and export the credentials to a JSON file. It also generates a PDF file with the necessary information.

- **Delete glass break access**: This option allows you to delete the service principal and invalidate the credentials file. It provides a warning before performing the deletion.

- **Validate credentials**: This option validates the credentials stored in the credentials file.

- **Renew secret key**: This option renews the secret key for the service principal and updates the credentials file with the new key.

- **Generate Vault PDF**: This option generates a PDF file with the necessary information for accessing the glass break vault. It uses the provided PDF template and CSS styling.

- **Provide emergency access**: This option provides emergency access by creating a user account, assigning it to an Azure AD role, and disabling conditional access policies.

- **Disable Conditional Access**: This option disables conditional access policies to allow emergency access.

- **Rollback emergency access/conditional access**: This option rolls back the changes made during emergency access by enabling conditional access policies and deleting the emergency user account.

## Automatic Tasks

The CLI application also supports automatic tasks using command line parameters:

- **Test break glass access**: You can test the break glass access functionality using the following command:

  ```shell
  python main.py -t -f /path/to/credentials.json
  ```

  This will test the break glass access functionality using the provided credentials file.

- **Renew the SP Token**: To renew the service principal token, use the following command:

  ```shell
  python main.py -r -f /path/to/credentials.json
  ```

  This will renew the service principal token using the provided credentials file.

You can modify and combine these command line parameters as per your requirements.

## License

This project is licensed under the [MIT License](LICENSE).
```

Feel free to modify the content and structure of the `README.md` file according to your project's specific needs.