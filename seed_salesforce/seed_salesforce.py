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
# future annotations to support typing when return the class (from a classmethod)
from __future__ import annotations

from pathlib import Path

from pyseed.seed_client import SeedClient

from seed_salesforce.salesforce_client import SalesforceClient

from datetime import datetime
import json


class SeedSalesforce(object):
    def __init__(self, seed_client: SeedClient = None, salesforce_client: SalesforceClient = None, labels: list = None, last_update: str = None, salesforce_account_record_type: str = None):
        self.seed = seed_client
        self.salesforce = salesforce_client
        # customized seed labels for salesforce workflow
        self.labels = labels
        # last update push to salesforce
        self.last_update = last_update
        # Account RecordTypeID
        self.salesforce_account_record_type = salesforce_account_record_type


    # @classmethod
    # def init_by_env_vars():
    #     # read settings from ENV vars, if passed
    #     seed_user = os.environ.get('SEED_USER', seed_user)
    #     seed_apikey = os.environ.get('SEED_APIKEY', seed_apikey)
    #     seed_protocol = os.environ.get('SEED_PROTOCOL', seed_protocol)
    #     seed_url = os.environ.get('SEED_URL', seed_url)
    #     seed_port = os.environ.get('SEED_PORT', seed_port)

    @classmethod
    def init_with_files(cls, seed_config_file: Path, salesforce_config_file: Path,
                        seed_org_id: int = None, seed_cycle_id: int = None) -> SeedSalesforce:
        """Create an instance of the SEED <-> Salesforce connector. You can create an instance without a SEED Org and
        Cycle, but they will need to be provided before operations can be made.

        Args:
            seed_config_file (Path): Path to SEED connection file
            salesforce_config_file (Path): Path to the Salesforce connection file
            seed_org_id (int): ID of the SEED Org to use if passed. Defaults to None.
            seed_cycle_id (int): ID of the SEED Cycle to use. Defaults to None.

        Returns:
            SeedSalesforce: returns the SeedSalesforce class
        """
        seed_client = SeedClient(seed_org_id, connection_config_filepath=seed_config_file)
        if seed_cycle_id:
            seed_client.cycle_id = seed_cycle_id

        if salesforce_config_file:
            sf_client = SalesforceClient(connection_config_filepath=salesforce_config_file)
        else:
            sf_client = None

        # get labels from config file
        seed_params = json.load(open(seed_config_file))
        labels = {}
        last_update = None
        if 'indication_label' in seed_params.keys():
            labels['indication_label'] = seed_params['indication_label']
        if 'violation_label' in seed_params.keys():
            labels['violation_label'] = seed_params['violation_label']
        if 'complied_label' in seed_params.keys():
            labels['complied_label'] = seed_params['complied_label']
        # get last read time (if exists)
        if 'last_update_timestamp' in seed_params.keys():
            last_update = seed_params['last_update_timestamp']
        # get default Account RecordTypeID for Salesforce
        if 'salesforce_account_record_type' in seed_params.keys():
            salesforce_account_record_type = seed_params['salesforce_account_record_type']


        return SeedSalesforce(seed_client, sf_client, labels, last_update, salesforce_account_record_type)

    def set_label(self, label_name: str, label_value: str):
        """ Store properties labels for use with Salesforce workflow

        Args:
            label_name (str):  The name of the indication label to use
        """
        self.labels[label_name] = label_value

    def set_last_update(self, last_update: str):
        """ Set the timestamp for the last update to Salesforce
        Args: last_update (str): String timestamp of last update, in format: yyyy-MM-dd HH:mm:ss.SSS
        """
        self.last_update = last_update

    def set_cycle_by_name(self, cycle_name: str):
        """Set the SEED cycle by name

        Args:
            cycle_name (str): Name of the SEED cycle to use
        """
        if self.seed.get_cycle_by_name(cycle_name, set_cycle_id=True):
            return True
        else:
            raise Exception(f'Unable to set the SEED cycle to {cycle_name}')

    def set_org_by_name(self, org_name: str):
        """Set the SEED cycle by name

        Args:
            org_name (str): Name of the organization to use
        """
        if self.seed.get_org_by_name(org_name, set_org_id=True):
            return True
        else:
            raise Exception(f'Unable to set the org to {org_name}')

    def get_org_by_name(self, org_name: str):
        """ Get the SEED Org name

        Args: 
            org_name (str): Name of the organization to use
        """

        return self.seed.get_org_by_name(org_name)


    def sync_properties_with_salesforce(self):
        """ Sync SEED properties with Salesforce

        Copying general workflow from here (minus OEP-specific things)
        https://github.com/SEED-platform/OEP/blob/develop/SEED%20Benchmark/OEI/pollseedforproperties.xml

        """

        # TODO: error logging

        # get all labels
        all_labels = self.seed.get_labels()
        # print(f"ALL labels: {all_labels}")

        # get properties list that have the 'Indication Label' label applied (for adding to Salesforce)
        sf_labels = self.seed.get_view_ids_with_label([self.labels['indication_label']])

        """ labels response looks like this (list):
        [
          {
            "id": 30,
            "name": "Add to Salesforce",
            "color": "orange",
            "organization_id": 2,
            "is_applied": [212],
            "show_in_list": false
          }
        ]
        """
        #print(f" SF label(s): {sf_labels}")

        # retrieve property details for each property with the 'Add to Salesforce' Label (list in is_applied)
        if sf_labels and sf_labels[0] and 'is_applied' in sf_labels[0].keys():
            for item in sf_labels[0]['is_applied']:
                # get property
                property = self.seed.get_property(item)
                print(f" property name: {property['state']['property_name']}, updated date: {property['property']['updated']}")

                # first check if Benchmark Salesforce ID exists on this record. we can't do anything otherwise
                if not property['state']['extra_data']['Benchmark Salesforce ID']:
                    # TODO: catch and log
                    print(f"""SEED record for Property: {property['state']['property_name']} has no Benchmark Salesforce ID populated. 
                        Create Record in Salesforce first and update SEED record with its Benchmark Salesforce ID.""")

                # compare date: property update date should be more recent than last Salesforce upload, otherwise skip.
                if self.compare_date_for_upload(property['state']['updated']) is True:
                    print(f"date comparison == UPDATE! for property {property['state']['property_name']}")

                    # figure out what other labels are applied to this property
                    # keep a comma-delimited list for upload to Salesforce later
                    labelNames = []
                    for label_id in property['labels']:
                        the_label = next((item for item in all_labels if item['id'] == label_id), None)
                        if the_label is None:
                            # OEP checks if a label applied doesn't exist in SEED and errors out
                            # TODO: log appropriately
                            print(f"""SEED Label: {label_id} assigned to Property: {property['state']['property_name']} has no details in SEED. 
                                 \n As a result the SEED property (SEED ID: {propertyId} will not be updated in Salesforce until the issue is resolved. 
                                 Confirm that the unavailable SEED label is removed from this property.""")
                            continue

                        labelNames.append(the_label['name'])

                    print(f"labelNames: {labelNames}")
                    labelNameString = ','.join(labelNames)
                    print(f"labelNameString: {labelNameString}")

                    # check if property is in violation
                    isInViolation = True if self.labels['violation_label'] in labelNames else False
                    isInCompliance = True if self.labels['complied_label'] in labelNames else False

                    # check violation / compliance status and ensure property should be uploaded
                    if (isInViolation and not isInCompliance) or (not isInViolation and isInCompliance):
                        # xor only one of the labels is applied, can push to Salesforce
                        print("Only one label from Violation and Complied is applied, property can be pushed to Salesforce!")

                        # QuerySFforContactAndAccount
                        # TODO: customizable per instance (looking up contact in Salesforce)?
                        contact_email = property['state']['extra_data']['Email'].strip()
                        contact_name = property['state']['extra_data']['On Behalf Of']
                        account_name = property['state']['extra_data']['Organization'].strip()

                        contact_record = self.get_create_contact(contact_name, contact_email, account_name)
                        print(f"contact record Id: {contact_record['Id']}, AccountId: {contact_record['AccountId']}")

                        # QuerySFforAdminContactAndAccount
                        data_admin_email = property['state']['extra_data']['Property Data Administrator - Email'].strip()
                        data_admin_name = property['state']['extra_data']['Property Data Administrator'].strip()

                        admin_contact_record = self.get_create_contact(data_admin_name, data_admin_email, account_name)
                        print(f"admin contact record Id: {admin_contact_record['Id']}, AccountId: {admin_contact_record['AccountId']}")

                        # TODO: test contact record now exists, log error and break if not

                        # PushPropertytoSalesforce
                        result = self.prepare_update_and_push(property, contact_record['Id'], admin_contact_record['Id'], labelNameString, isInViolation, isInCompliance)

                    elif isInViolation and isInCompliance:
                        # Both of these labels should not be applied, ERROR
                        # TODO: log this appropriately
                        print(f"Property {property['state']['property_name']} has both labels {self.labels['violation_label']} and {self.labels['complied_label']} applied. It should only have one of them. The property was not uploaded to Salesforce.")

                    else:
                        # Neither label is applied
                        # TODO: log this appropriately
                        print(f"Property {property['state']['property_name']} is missing one of the following labels: {self.labels['violation_label']} or {self.labels['complied_label']}. It was not uploaded to Salesforce.")


    def get_create_contact(self, name: str, email: str, account_name: str):
        """ Retrieve or Create an account and contact for person associated with a property (either data admin or property contact)

        Args:
            name (str): contact name
            email (str): contact email (primary key)
            account_name (str): organization account name

        Returns: contact_record, which contains Id (contactId) and AccountId
        Note: maybe use a template similar to render_mapping for this?
        """
        
        contact_record = self.salesforce.find_contact_by_email(email)
        # print(f"contact returned: {contact_record}")
        # TODO: extract account Id and return that too?

        if not contact_record:
            # CreateContactAndAccount
            account_record = self.salesforce.find_account_by_name(account_name)
            # print(f"account record: {account_record}")
            if not account_record:
                # make account
                account_record = self.salesforce.create_account(account_name, RecordTypeId=self.salesforce_account_record_type)
                # print(f"created account record: {account_record}")
                # TODO: check account has ID if not log error

            account_id = account_record['Id']
            contact_record = self.salesforce.create_contact(email, AccountId=account_id, LastName=name)
            # print(f"contact record: {contact_record}")

        # TODO: error catching / logging here

        return contact_record

    def prepare_update_and_push(self, property: dict, contact: str, admin_contact: str, label_name_string: str, isInViolation: bool, isInCompliance: bool):
        """ Prepare data for update and push to Salesforce
            
        Args: 
            property (dict): property response from seed api
            contact (str): salesforce contact id
            admin_contact (str): salesforce admin contact id
            labelNameString (str): string of all label names 
            isInViolation (bool): record labeled with violation T of F
            isInCompliance (bool): record labeled with complied T or F

        Returns:
        """

        # Map In Violation Property To Benchmark    
        context = {}
        context['contactResults'] = contact
        context['adminContactResults'] = admin_contact
        context['property'] = property
        context['labelNameString'] = label_name_string

        salesforce_id = property['state']['extra_data']['Benchmark Salesforce ID']

        if isInViolation:
            # create context and pass in to template
            print("VIOLATION! UPDATE PROPERTY NOT BENCHMARK?")
            context['statusLabel'] = self.labels['violation_label']
            result = self.salesforce.render_mappings('property-isinviolation.json.template', context)
            print(f"RESULTING TEMPLATE LOOKS LIKE THIS: {result}")
            print(f"!!!!! salesforceID: {salesforce_id}, result: {result}")
            # objs = self.salesforce.list_objects()
            print(f"len of result: {len(result)}")
            response = self.salesforce.update_benchmark(salesforce_id, result)

        else:
            if isInCompliance:
                context['statusLabel'] = self.labels['complied_label']
            else:
                context['statusLabel'] = None

            print(f"STATUS LABEL: {context['statusLabel']}")
            # create context and pass in to template
            result = self.salesforce.render_mappings('property-complied.json.template', context)
            response = self.salesforce.update_benchmark(salesforce_id, result)


    def get_last_process_date(self):
        """ Returns last update to Salesforce date string and convert to date object for comparison
        """

        if self.last_update is None:
            last_update_date_obj = datetime.strptime('2001-01-01 12:00:00.000-07:00', '%Y-%m-%d %H:%M:%S.%f%z')
        else:
            last_update_date_obj = datetime.strptime(self.last_update, '%Y-%m-%d %H:%M:%S.%f%z')

        #last_update_date_obj.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return last_update_date_obj

    def compare_date_for_upload(self, seed_updated_date: str):
        """ Compare SEED property date with last upload to Salesforce date. 
        Return true if property should be updated in Salesforce, false if not.

        Args:
            seed_updated_date (str): the property's 'updated' date in format '%Y-%m-%dT%H:%M:%S.%f%z'
        """
        last_update_date_obj = self.get_last_process_date()
        print(f"LAST UPDATE DATE: {last_update_date_obj}")
        # SEED updated date example: '2022-10-28T20:24:31.426330Z'
        seed_updated_date_obj = datetime.strptime(seed_updated_date, '%Y-%m-%dT%H:%M:%S.%f%z')
        print(f"SEED UPDATED DATE: {seed_updated_date_obj}")
        
        return True if (seed_updated_date_obj > last_update_date_obj) else False


    def upload_attachment(self, attachment_path: Path, attachment_name: str):
        """Upload an attachment to Salesforce

        Args:
            attachment_path (Path): Path to the attachment to upload
            attachment_name (str): Name of the attachment to upload
        """
        # see https://stackoverflow.com/questions/60304958/upload-pdf-from-python-as-attachment-to-salesforce-object
        self.salesforce.upload_attachment(attachment_path, attachment_name)

    def run_on_interval(wait_time: int = 3600):
        """Run the _run_ method every `wait_time` seconds

        Args:
            wait_time (int, optional): time between runs, in seconds. Defaults to 3600.
        """
        #     - name: OEP_CRON_TIMER
        #       value: "0 0 0/1 ? * * *"
        pass
