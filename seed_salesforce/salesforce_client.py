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

_log = logging.getLogger(__name__)


class SalesforceClient(object):
    def __init__(self, connection_params: dict = None, connection_config_filepath: Path = None) -> None:
        """Connection to salesforce. Uses the `simple_salesforce` library to communicate with Salesforce.

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

    def list_objects(self) -> list:
        """ List all objects in salesforce db 
        Returns:
            list of objects
        """

        objects = self.connection.query("SELECT SObjectType FROM ObjectPermissions GROUP BY SObjectType ORDER BY SObjectType ASC")
        #print(f"OBJECTS: \n {objects}")

        # temp: get all fields for Property
        # props = self.connection.query("SELECT FIELDS(ALL) FROM Property__c LIMIT 1")
        # print(f"\n\n PROPERTY FIELDS ARE: {props}")

        # temp: get all fields for Benchmark
        # benchmarks = self.connection.query("SELECT FIELDS(ALL) FROM Benchmark__c LIMIT 1")
        # print(f"\n\n BENCHMARK FIELDS ARE: {benchmarks}")

        fields = self.connection.query("SELECT EntityDefinition.QualifiedApiName, QualifiedApiName, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'oei__Benchmark__c'")
        print(f"\n\n FIELDS: {fields}")
        return objects

    def get_first_benchmark(self) -> dict:
        """Get a benchmark (for testing mainly)

        Returns:
            dict:  OrderedDict([('attributes', 
            OrderedDict([('type', 'Benchmark__c'), 
            ('url', '/services/data/v52.0/sobjects/Benchmark__c/a0156000004bOpHAAU')])), 
            ('Id', 'a0156000004bOpHAAU'),
            ...
        """
        response = self.connection.query(f"Select FIELDS(ALL) from Benchmark__c limit 1")
        if response:
            if response['totalSize'] > 0:
                return response['records'][0]
            else:
                # no records?
                raise Exception(f"There are no Benchmark records to return")
        else:
            raise Exception(f"Failed to return a Benchmark")

    def get_benchmark_by_custom_id(self, salesforce_benchmark_id: str) -> dict:
        """Return the benchmark by the Salesforce Benchmark ID.

        Args:
            salesforce_benchmark_id (str): Salesforce Benchmark ID of the property to return
            Note: this is not necessarily the Benchmark ID (it's a separate field)
            # TODO: make this configurable?

        Returns:
            dict:  OrderedDict([('attributes', 
            OrderedDict([('type', 'Benchmark__c'), 
            ('url', '/services/data/v52.0/sobjects/Benchmark__c/a0156000004bOpHAAU')])), 
            ('Id', 'a0156000004bOpHAAU'),
            ...
        """
        
        benchmark_exist = self.connection.query(f"Select Id from Benchmark__c where Salesforce_Benchmark_ID__c = '{salesforce_benchmark_id}'")
        if len(benchmark_exist['records']) == 1:
            # if there is a single record, then it exist, but
            # we need to get the entire record for the request
            rec = self.get_benchmark_by_id(benchmark_exist['records'][0]['Id'])
            return rec
        elif len(benchmark_exist['records']) > 1:
            # there are multiple properties with the same name, raise error
            raise Exception(f"Failed to retrun Benchmark {salesforce_benchmark_id}...multiple benchmarks with that name found")
        else:
            # there is no property, return empty dict
            return {}

    def get_benchmark_by_id(self, benchmark_id: str) -> dict:
        """Return the benchmark by the salesforce benchmark ID (not custom field).

        Args:
            benchmark_id (str): ID of the benchmark to return

        Returns:
            dict:  OrderedDict([('attributes', 
            OrderedDict([('type', 'Benchmark__c'), 
            ('url', '/services/data/v52.0/sobjects/Benchmark__c/a0156000004bOpHAAU')])), 
            ('Id', 'a0156000004bOpHAAU'),
            ...
        """
        try:
            return self.connection.Benchmark__c.get(benchmark_id)
        except:
            raise Exception("Error retrieving benchmark by ID")

    def update_benchmark(self, salesforce_benchmark_id, **kwargs) -> dict:
        """ Update an existing benchmark

        Args:
            salesforce_benchmark_id (str): special field serving as Unique Key for retrieving this benchmark object
            (we are not using the property's ID)

        Returns:
            dict: OrderedDict([...])
        """
        # TODO: try it with the customExtIdField__c/11999 syntax here
        # otherwise: get the Id from salesforce_benchmark_id and then update

        updated_record = self.connection.Benchmark__c.update(salesforce_benchmark_id,  {
            **kwargs
        })
        print(f"response: {updated_record}")

        if updated_record == 204:
            # TODO: we are making an assumption here that salesforce_benchmark_id is also the Benchmark's ID
            # make a better "get" using the field "Salesforce_Benchmark_ID__c" instead of "Id"
            # TODO: Is it necessary for us to pass around these whole objects?
            # benchmark = self.connection.Benchmark__c.get(salesforce_benchmark_id)
            # return benchmark
            return updated_record
        else:
            raise Exception(f"Failed to update Benchmark {salesforce_benchmark_id} with error: {updated_record['errors']}")

    def update_property(self, property_id: str, **kwargs) -> dict:
        """Update an existing Property.

        Args:
            property_id (str): id of contact to update
            **kwargs: additional parameters to update

        Raises:
            Exception: Error updating record

        Returns:
            dict: OrderedDict([...])
        """
        updated_record = self.connection.Property__c.update(property_id, {
            **kwargs
        })

        if updated_record == 204:
            prop = self.connection.Property__c.get(property_id)
            return prop
        else:
            raise Exception(f"Failed to update property {property_id} with error: {updated_record['errors']}")


    def get_first_property(self) -> dict:
        """Get a property (for testing mainly)

        Returns:
            dict: OrderedDict([('attributes', 
            OrderedDict([('type', 'Property__c'), 
            ('url', '/services/data/v52.0/sobjects/Property__c/a0256000005mDNrAAM')])), 
            ('Id', 'a0256000005mDNrAAM'),
            ...
        """
        prop = self.connection.query(f"Select FIELDS(ALL) from Property__c limit 1")
        if prop:
            if prop['totalSize'] > 0:
                return prop['records'][0]
            else:
                # no records
                return {}
        else:
            raise Exception(f"Failed to return a property")

    def find_property_by_name(self, name: str) -> dict:
        """Retrieve an existing Property by name 
        Args: 
            name (str): name of the property

        Returns: 
            dict: OrderedDict([(
            'attributes', OrderedDict([('type', 'Property__c'), 
            ('url', '/services/data/v52.0/sobjects/Property__c/a0056000005SoEiAAK')])), 
            ('Id', 'a0056000005SoEiAAK'), 
            ('Name', '123 Made Up St'),
            ...
        """

        # clean name
        name = name.strip().replace("'", "\\'")

        property_exist = self.connection.query(f"Select Id from Property__c where Name = '{name}'")
        if len(property_exist['records']) == 1:
            # if there is a single record, then it exist, but
            # we need to get the entire record for the request
            prop = self.get_property_by_id(property_exist['records'][0]['Id'])
            return prop
        elif len(property_exist['records']) > 1:
            # there are multiple properties with the same name, raise error
            raise Exception(f"Failed to return Property {name}...multiple properties with that name found")
        else:
            # there is no account, return empty dict
            return {}

    def get_property_by_id(self, property_id: str) -> dict:
        """Return the property by the salesforce property ID.

        Args:
            property_id (str): ID of the property to return

        Returns:
            dict: OrderedDict([(
            'attributes', OrderedDict([('type', 'Property__c'), 
            ('url', '/services/data/v52.0/sobjects/Property__c/a0056000005SoEiAAK')])), 
            ('Id', 'a0056000005SoEiAAK'), 
            ('Name', '123 Made Up St'),
            ...
        """
        try:
            return self.connection.Property__c.get(property_id)
        except:
            raise Exception("Error retrieving property by ID")

    def get_account_by_account_id(self, account_id: str) -> dict:
        """Return the account by the account ID.

        Args:
            account_id (str): ID of the account to return

        Returns:
            dict: {
                Account info...
            }
        """
        return self.connection.Account.get(account_id)

    def find_account_by_name(self, name: str) -> dict:
        """Find a record on the Account table by passed name.

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

        # clean name
        name = name.strip().replace("'", "\\'")

        account_exist = self.connection.query(f"Select Id from Account where Name = '{name}'")
        if len(account_exist['records']) == 1:
            # if there is a single record, then it exist, but
            # we need to get the entire record for the request
            account = self.get_account_by_account_id(account_exist['records'][0]['Id'])
            return account
        else:
            # there is no account, return empty dict
            return {}

    def create_account(self, name: str, **kwargs) -> dict:
        """Create a record on the Account table.

        Args:
            name (str): name of the account to create
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
        account = self.find_account_by_name(name)
        if account:
            raise Exception(f"Account {name} already exists.")
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
                raise Exception(f"Failed to create account {name} with error: {new_record['errors']}")

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

    def update_contact(self, contact_id: str, **kwargs) -> dict:
        """Update an existing Contact.

        Args:
            contact_id (str): id of contact to update
            **kwargs: additional parameters to update

        Raises:
            Exception: Error updating record

        Returns:
            dict: OrderedDict([
        """
        updated_record = self.connection.Contact.update(contact_id, {
            **kwargs
        })

        if updated_record == 204:
            account = self.connection.Contact.get(contact_id)
            return account
        else:
            raise Exception(f"Failed to update contact {email} with error: {updated_record['errors']}")


    def update_account_by_id(self, account_id: str, update_data: dict) -> dict:
        """Update the fields of an existing account on Salesforce

        Args:
            account_id (str): id of the salesforce account to delete
            update_data (dict): fields to update on Salesforce account

        Returns:
            dict: updated account record
        """
        return self.connection.Account.update(account_id, update_data)

    def delete_account_by_id(self, id: str) -> bool:
        """Delete a record on the Account table by passed id.

        Args:
            id (str): id of the salesforce account to delete

        Returns:
            bool: did the account get deleted successfully?
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

        return {}

    def create_or_update_contact_on_account(self, contact_email: str, **kwargs) -> dict:

        # find the contact
        contact = self.find_contact_by_email(contact_email)

        if not contact:
            # create and assign to account
            contact = self.create_contact(contact_email, **kwargs)
        else:
            # update contact with name and account Id, etc?
            contact = self.update_contact(contact['Id'], **kwargs)

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
