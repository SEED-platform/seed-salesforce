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
        assert sf.connection.base_url is not None

    def test_render_mappings(self):
        config_file = Path('salesforce-config-dev.json')
        sf = SalesforceClient(connection_config_filepath=config_file)
        
        context = {
            "labels": "",
            "address": "123 Main St",
            "city": "Springfield",
            "state": "Unknown",
            "postal_code": "80401",
        }
        result = sf.render_mappings('seed-salesforce-benchmarking.json.template', context)
        assert result['ShippingStreet'] == '123 Main St'
        assert result['ShippingCity'] == 'Springfield'
        assert result['ShippingState'] == 'Unknown'


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
        return super().setUp()

    def test_search_and_create_and_delete_property(self):
        test_property_name = 'Scrumptious Ice Cream'
        account = self.sf.find_properties_by_name(test_property_name)
        # The first time should not have any results
        assert not account

        details = {
            'Type': 'Ice Cream Shop',
            'Phone': '555-867-5309',
            'Website': 'http://www.scrumptiousco.com',
        }
        account = self.sf.create_property(test_property_name, **details)
        account_id = account['Id']
        assert account['Name'] == test_property_name
        assert account['Type'] == 'Ice Cream Shop'
        assert account_id is not None

        # Find the record
        account = self.sf.find_properties_by_name(test_property_name)
        assert account['Id'] == account_id

        # now delete it to cleanup
        success = self.sf.delete_property_by_id(account_id)
        assert success

    def test_custom_field(self):
        self.sf.create_custom_field('TestField', 255, 'Just enter something here for testing')

    def test_write_to_salesforce(self):
        account = self.sf.find_properties_by_name(self.test_org)
        account_id = account['Id']

        self.sf.update_property_by_id(account_id, {
            'AccountNumber': '4815162343',
        })

        self.sf.create_or_update_contact_on_account('user@company.com', 'Richard', 'Hendrick', account_id)
