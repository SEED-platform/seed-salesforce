"""
****************************************************************************************************
:copyright (c) 2019-2022, Alliance for Sustainable Energy, LLC, and other contributors.

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions
and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this list of conditions
and the following disclaimer in the documentation and/or other materials provided with the
distribution.

Neither the name of the copyright holder nor the names of its contributors may be used to endorse
or promote products derived from this software without specific prior written permission.

Redistribution of this software, without modification, must refer to the software by the same
designation. Redistribution of a modified version of this software (i) may not refer to the
modified version by the same designation, or by any confusingly similar designation, and
(ii) must refer to the underlying software originally provided by Alliance as “URBANopt”. Except
to comply with the foregoing, the term “URBANopt”, or any confusingly similar designation may
not be used to refer to any modified version of this software or any modified version of the
underlying software originally provided by Alliance without the prior written consent of Alliance.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
****************************************************************************************************
"""

import json
import logging
from pathlib import Path

import requests
from simple_salesforce import Salesforce
from jinja2 import Environment, FileSystemLoader, StrictUndefined

_log = logging.getLogger(__name__)


class SalesforceClient(object):
    def __init__(self, connection_params: dict = None, connection_config_filepath: Path = None) -> None:
        """Connection to salesforce. Uses the `simple_salesforce` library to commnicate with Salesforce.

        Args:
            connection_params (dict, optional): Parameters to connect to Salesforce. Defaults to None. If using, then must contain:
                {
                    "instance": "https://<environment>.lightning.force.com",
                    "username": "user@somedomain.com",
                    "password": "alongpassword",
                    "security_token": "access1key2with3numbers"
                }
            connection_config_filepath (Path, optional): Path to the file to read the parameters from. Defaults to None.

        Raises:
            Exception: File not found
        """
        self.session = requests.Session()

        connect_info = {}
        if connection_params:
            connect_info = connection_params
        elif connection_config_filepath:
            connect_info = SalesforceClient.read_connection_config_file(connection_config_filepath)
        else:
            raise Exception("Must pass either the connection params as a dict, or a file with the connection credentials.")

        self.connection = Salesforce(
            **connect_info,
            session=self.session
        )
        self.mdapi = self.connection.mdapi

        self._template_dir = Path(__file__).parent / "default_mappings"
        if not Path(self._template_dir).exists():
            raise Exception(f'Invalid coupling. Missing {self._template_dir} directory.')

        self._template_env = Environment(
            loader=FileSystemLoader(searchpath=self._template_dir),
            undefined=StrictUndefined)

    @classmethod
    def read_connection_config_file(cls, filepath: Path) -> dict:
        """Read in the connection config file and return the connection params. The format in the file must incude:

            {
                "instance": "https://<environment>.lightning.force.com",
                "username": "user@somedomain.com",
                "password": "alongpassword",
                "security_token": "access1key2with3numbers"
            }

        Args:
            filepath (str): path to the connection config file
        """
        if not filepath.exists():
            raise Exception(f"Cannot find connection config file: {str(filepath)}")

        connection_params = json.load(open(filepath))
        return connection_params

    def render_mappings(self, template_name: str, context) -> dict:
        """Render the mappings template.

        Args:
            template_name (str): name of the template file to render
            context (dict): context to render the template with

        Returns:
            dict: rendered mappings in a dictionary format, meaning that the
            rendered file is loaded into memory and returned as a dictionary.
        """
        rendered = self._template_env.get_template(template_name).render(context)
        return json.loads(rendered)


    def get_property_by_account_id(self, account_id: str) -> dict:
        """Return the property by the account ID.

        Args:
            account_id (str): ID of the account to return

        Returns:
            dict: {
                Account info...
            }
        """
        return self.connection.Account.get(account_id)

    def find_properties_by_name(self, name: str) -> dict:
        """Find a property on the Account table by passed name.

        Args:
            name (str): name of the account to find

        Returns:
            dict: OrderedDict([
                ('attributes', OrderedDict([('type', 'Account'), ('url', '/services/data/v52.0...01qmgddAAA')])),
                ('Id', '0018a00001qmgddAAA'),
                ('IsDeleted', False),
                ('MasterRecordId', None),
                ('Name', 'Scrumptious Ice Cream'),
                ('Type', 'Ice Cream Shop'),
        """
        account_exist = self.connection.query(f"Select Id from Account where Name = '{name}'")
        if len(account_exist['records']) == 1:
            # if there is a single record, then it exist, but
            # we need to get the entire record for the request
            account = self.get_property_by_account_id(account_exist['records'][0]['Id'])
            return account
        else:
            # there is no property, return empty dict
            return {}

    def create_property(self, name: str, **kwargs) -> dict:
        """Create a property on the Account table.

        Args:
            name (str): name of the property to create
            **kwargs: additional parameters to pass to the create method

        Raises:
            Exception: Property not found
            Exception: Error creating record

        Returns:
            dict: OrderedDict([
                ('attributes', OrderedDict([('type', 'Account'), ('url', '/services/data/v52.0...01qmgddAAA')])),
                ('Id', '0018a00001qmgddAAA'),
                ('IsDeleted', False),
                ('MasterRecordId', None),
                ('Name', 'Scrumptious Ice Cream'),
                ('Type', 'Ice Cream Shop'),
        """
        account = self.find_properties_by_name(name)

        if account:
            raise Exception(f"Property {name} already exists.")
        else:
            new_record = self.connection.Account.create({
                'Name': name,
                **kwargs
            })
            if new_record['success']:
                # The new_record is now just a "success" type recall with an ID. We
                # want to return the full record, so now "get" the record.
                account = self.connection.Account.get(new_record['id'])
                return account
            else:
                raise Exception(f"Failed to create property {name} with error: {new_record['errors']}")

    def create_contact(self, email: str, **kwargs) -> dict:
        """Create a contact on the Contact table.

        Args:
            name (str): email of the contact to create
            **kwargs: additional parameters to pass to the create method

        Raises:
            Exception: Property not found
            Exception: Error creating record

        Returns:
            dict: OrderedDict([
        """
        account = self.find_contact_by_email(email)

        if account:
            raise Exception(f"Contact {email} already exists.")
        else:
            new_record = self.connection.Contact.create({
                'Email': email,
                **kwargs
            })
            if new_record['success']:
                # The new_record is now just a "success" type recall with an ID. We
                # want to return the full record, so now "get" the record.
                account = self.connection.Contact.get(new_record['id'])
                return account
            else:
                raise Exception(f"Failed to create contact {email} with error: {new_record['errors']}")

    def update_property_by_id(self, account_id: str, update_data: dict) -> dict:
        """Update the fields of an existing property on Salesforce

        Args:
            account_id (str): id of the salesforce account to delete
            update_data (dict): fields to update on Salesforce account

        Returns:
            dict: updated account record
        """
        return self.connection.Account.update(account_id, update_data)

    def delete_property_by_id(self, id: str) -> bool:
        """Delete a property on the Account table by passed id.

        Args:
            id (str): id of the salesforce account to delete

        Returns:
            bool: did the property get deleted successfully?
        """
        status = self.connection.Account.delete(id)
        if status == 204:
            return True
        else:
            return False

    def find_contact_by_email(self, email: str) -> dict:
        """Find the contact in the Salesforce contact table and return the info

        Args:
            email (str): email of the conact to find. Email must be unique across the entire system

        Returns:
            dict: dictionary of contact information
        """
        contact_info = self.connection.query(f"Select Id, Email, Account.Name from Contact where Email = '{email}'")
        if len(contact_info['records']) == 1:
            # contact exists, return the full record
            return self.connection.Contact.get(contact_info['records'][0]['Id'])

        return None

    def create_or_update_contact_on_account(self, contact_email: str, contact_first_name: str, contact_last_name: str, account_id: str) -> dict:

        # find the contact
        contact = self.find_contact_by_email(contact_email)
        if not contact:
            contact = self.create_contact(contact_email, FirstName=contact_first_name, LastName=contact_last_name)

        # get the account record
        self.get_property_by_account_id(account_id)
        # figure out how to add the contact to the account

        # self.update_property_by_id(account_id, {'Contact__c': contact['Id']})

        # TODO: need to figur out how to assign a contact
        return None

    def create_custom_field(self, object_name: str, field_name: str, length: int, description: str) -> dict:
        """Right now this only creates a new string field of "LongTextArea"

        Args:
            object_name (str): Name of the salesforce object (table), e.g., Account, Benchmarking
            field_name (str): Name of the field to create with no spaces
            length (int): Length of field
            description (str): Description of the field

        Returns:
            dict: _description_
        """        
        length = 256 if length < 256 else length

        # check if the field already exists
        custom_field = self.mdapi.CustomField(
            label=field_name,
            fullName=f"{object_name}.{field_name}__c",
            type=self.mdapi.FieldType("LongTextArea"),
            length=length,
            description=description,
            visibleLines=25
        )
        return self.mdapi.CustomField.create(custom_field)

    #     custom_object = mdapi.CustomObject(
    #     fullName = "CustomObject__c",
    #     label = "Custom Object",
    #     pluralLabel = "Custom Objects",
    #     nameField = mdapi.CustomField(
    #         label = "Name",
    #         type = mdapi.FieldType("Text")
    #     ),
    #     deploymentStatus = mdapi.DeploymentStatus("Deployed"),
    #     sharingModel = mdapi.SharingModel("Read")
    # )
