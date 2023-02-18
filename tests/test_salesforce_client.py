"""
****************************************************************************************************
:copyright (c) 2022, Alliance for Sustainable Energy, LLC, and other contributors.

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

import unittest
from pathlib import Path

from seed_salesforce.salesforce_client import SalesforceClient


class SalesforceClientTest(unittest.TestCase):
    def test_init_by_file(self):
        config_file = Path('salesforce-config-dev.json')
        sf = SalesforceClient(connection_config_filepath=config_file)
        # check if the Salesforce connection has the base_url method and that it is not None
        assert hasattr(sf.connection, 'base_url')
        print(f"sf connection: {sf.connection.base_url}")
        assert sf.connection.base_url is not None


class SalesforceIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path('tests/output')
        if not self.output_dir.exists():
            self.output_dir.mkdir()

        # create the connection to salesforce.
        # These tests run against a development version of Salesforce
        config_file = Path('salesforce-config-dev.json')
        self.sf = SalesforceClient(connection_config_filepath=config_file)

        self.test_org = "New Test Account"
        self.test_email = "a-user@somecompany.com"
        self.test_benchmark_name = "Example Benchmarking"
        self.account_record_type = None
        self.contact_record_type = "01256000003A9ZN"

        return super().setUp()

    def test_search_and_create_and_delete_account(self):
        test_account_name = 'Scrumptious Ice Cream'
        account = self.sf.find_account_by_name(test_account_name)
        # The first time should not have any results
        assert not account

        details = {
            'Type': 'Ice Cream Shop',
            'Phone': '555-867-5309',
            'Website': 'http://www.scrumptiousco.com',
        }
        if self.account_record_type:
            details['RecordTypeID'] = self.account_record_type

        account = self.sf.create_account(test_account_name, **details)
        account_id = account['Id']
        # print(f"ACCOUNT ID: {account_id}")
        assert account['Name'] == test_account_name
        assert account['Type'] == 'Ice Cream Shop'
        assert account_id is not None

        # Find the record
        account = self.sf.find_account_by_name(test_account_name)
        assert account['Id'] == account_id

        # now delete it to cleanup
        success = self.sf.delete_account_by_id(account_id)
        assert success


    def test_update_contact_and_account(self):
        test_account_name = 'A Fake Account'
        details = {
            'Type': 'Office',
            'Phone': '555-867-5309',
            'Website': 'http://www.scrumptiousco.com'
        }
        if self.account_record_type:
            details['RecordTypeID'] = self.account_record_type

        account = self.sf.create_account(test_account_name, **details)
        account_id = account['Id']

        success = self.sf.update_account_by_id(account_id, {
            'Phone': '444-444-4444',
            'Website': 'http://www.UpdatedWebsite.com'
        })
        # this returns a 204 but seems to do so regardless of whether property exists
        assert success

        # contacts
        # create contact (associated with account)
        details = {
            'AccountId': account_id,
            'LastName': 'Richard Hendrick'
        }
        if self.contact_record_type:
            details['RecordTypeID'] = self.contact_record_type

        self.sf.create_contact('user@company.com', **details)
        # retrieve contact
        contact = self.sf.find_contact_by_email('user@company.com')
        assert contact['AccountId'] == account_id 

        # update contact (can't change email)
        details = {
            'AccountId': account_id,
            'LastName': 'Russ Hanneman'
        }
        self.sf.create_or_update_contact_on_account('user@company.com', **details)
        assert contact['AccountId'] == account_id 

        # now delete it to cleanup
        success = self.sf.delete_account_by_id(account_id)
        assert success

    # Note: Keeping this for posterity but we do not use this functionality currently in SEED
    # def test_property(self):
    #     # assumes there is a property in salesforce already

    #     # random field to update
    #     new_year_built = "2000"
    #     args = {"Year_Built__c": new_year_built}

    #     # can you get a property (return first one)
    #     print(f" ...get first property (to get an ID)...")
    #     prop = self.sf.get_first_property()
    #     print(f" prop: {prop}")
    #     assert prop is not None
    #     property_id = prop['Id']
    #     property_name = prop['Name']
    #     # we are assuming this exists I guess it might not
    #     year_built = prop['Year_Built__c']
    #     print(f" Using property Id: {property_id}")

    #     # can you retrieve by property ID?
    #     print(f" ...retrieving property by property ID...")
    #     prop_by_id = self.sf.get_property_by_id(property_id)
    #     print(f" prop by id: {prop_by_id}")
    #     assert prop_by_id['Id'] == property_id

    #     # can you retrieve property by Name?
    #     print(f" ...retrieving property by name...")
    #     prop_by_name = self.sf.find_property_by_name(property_name)
    #     print(f" prop by name: {prop_by_name}")
    #     assert prop_by_name['Name'] == property_name

    #     # can you update a property field?
    #     print(f" ...updating property...")
    #     prop_updated = self.sf.update_property(property_id, **args)
    #     print(f"prop updated: {prop_updated}")
    #     assert prop_updated['Year_Built__c'] == new_year_built

    #     # restore value
    #     args['Year_Built__c'] = year_built
    #     prop_updated2 = self.sf.update_property(property_id, **args)

    def test_benchmark(self):

        # get first benchmark (to get an Id)
        print(f" ...get first benchmark (to get an ID)...")
        benchmark = self.sf.get_first_benchmark()
        print(f" Benchmark: {benchmark}")
        assert benchmark is not None
        benchmark_id = benchmark['Id']
        salesforce_benchmark_id = benchmark['Salesforce_Benchmark_ID__c']

        # can you retrieve by "Salesforce Benchmark ID" custom field?
        print(f" ...retrieving benchmark by Salesforce Benchmark ID...")
        bench_by_custom_id = self.sf.get_benchmark_by_custom_id(salesforce_benchmark_id)
        print(f" benchmark by custom id: {bench_by_custom_id}")
        assert bench_by_custom_id['Id'] == benchmark_id

        # can you update a benchmark field?
        print(f" ...updating benchmark...")
        # TODO: again assuming this field exists...it might not?
        ENERGY_STAR_Score = benchmark['ENERGY_STAR_Score__c']
        new_ENERGY_STAR_Score = 20
        args = {"ENERGY_STAR_Score__c": new_ENERGY_STAR_Score}
        bench_updated = self.sf.update_benchmark(salesforce_benchmark_id, **args)
        print(f"benchmark updated: {bench_updated}")

        # retrieve again to see if it was updated
        bench2 = self.sf.get_benchmark_by_custom_id(salesforce_benchmark_id)
        assert bench2['ENERGY_STAR_Score__c'] == new_ENERGY_STAR_Score

        # restore value
        args['ENERGY_STAR_Score__c'] = ENERGY_STAR_Score
        bench_updated2 = self.sf.update_benchmark(salesforce_benchmark_id, **args)
