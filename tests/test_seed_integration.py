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

import unittest
from datetime import date
from pathlib import Path

from dateutil.parser import parse

from seed_salesforce.seed_salesforce import SeedSalesforce
from seed_salesforce.salesforce_client import SalesforceClient


class SeedIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        sf_config = Path('salesforce-config-dev.json')
        seed_config = Path('seed-config-dev.json')

        self.client = SeedSalesforce.init_with_files(seed_config_file=seed_config, salesforce_config_file=sf_config)
        # print(f"ORG ID IS: {self.client.seed.get_org_id()}")

        # no longer setting org name outside of seed-config-dev.json file
        # self.client.set_org_by_name('test-org')

        self.sf = SalesforceClient(connection_config_filepath=sf_config)

        return super().setUp()

    def test_upload_single_method(self):
        # Get/create the new cycle and upload the data. Make sure to set the cycle ID so that the
        # data end up in the correct cycle
        self.client.seed.get_or_create_cycle(
            'single step upload',
            parse('6/1/2021').date(),
            parse('6/1/2022').date(),
            set_cycle_id=True)

        result = self.client.seed.upload_and_match_datafile(
            'single-step-test',
            'tests/data/test-seed-data.xlsx',
            'Single Step Column Mappings',
            'tests/data/test-seed-data-mappings.csv')

        assert result is not None
   
    def test_create_label(self):
        # create some labels and assign them to some records
        self.client.seed.get_or_create_label('Upload to Salesforce', 'light blue')

        labels = self.client.seed.get_labels(['Upload to Salesforce'])
        # print(f"LABELS: {labels}")
        assert labels is not None

    def test_assign_label_and_retrieve_bldgs_by_label(self):
        # set cycle
        cycle = self.client.seed.get_or_create_cycle(
            'single step upload', 
            parse('6/1/2021').date(),
            parse('6/1/2022').date(),
            set_cycle_id=True)

        # assign label to first record
        bldgs = self.client.seed.get_buildings()
        the_bldg = bldgs[0]
        self.client.seed.update_labels_of_buildings(['Upload to Salesforce'], [], [the_bldg['property_view_id']])

        # find the records with the label
        labeled_bldgs = self.client.seed.get_view_ids_with_label(['Upload to Salesforce'])
        # print(f"LABELED bldgs is_applied IDs: {labeled_bldgs[0]['is_applied']}, first bldg id: {the_bldg['property_view_id']}")
        assert the_bldg['property_view_id'] in labeled_bldgs[0]['is_applied']

    def test_sync_with_salesforce(self):
        # sync with salesforce
        
        # set cycle
        cycle = self.client.seed.get_or_create_cycle(
            'single step upload', 
            parse('6/1/2021').date(),
            parse('6/1/2022').date(),
            set_cycle_id=True)

        # assign label to first record
        bldgs = self.client.seed.get_buildings()
        the_bldg = bldgs[0]
        # print(f"bldg: {the_bldg}")
        self.client.seed.update_labels_of_buildings(['Upload to Salesforce'], [], [the_bldg['property_view_id']])

        # find the records with the label
        labeled_bldgs = self.client.seed.get_view_ids_with_label(['Upload to Salesforce'])

        bldgs_to_sf = []
        for l in labeled_bldgs:
            # loop through and get all labeled buildings
            for id in l['is_applied']:
                find_bldg = next((item for item in bldgs if item['property_view_id'] == id), None)
                if find_bldg:
                    bldgs_to_sf.append(find_bldg)

        print(f"found the following buildings to add to salesforce: {[d['property_view_id'] for d in bldgs_to_sf]}")
        
        for item in bldgs_to_sf:
            item['labels'] = ""  # TODO: do we need specific labels here? all of the building's labels?

            # see if this building is in salesforce already (using property_name as unique ID for now)
            # this would probably all be configured a different way?
            # TODO: need to figure out the "unique identifer" to find a property in salesforce
            # print(f"item.items(): {item.items()}")
            property_name = next( v for k,v in item.items() if k.startswith('property_name_'))

            # print(f"propertyname: {property_name}")
            item['property_name'] = property_name
            for field in ['address_line_1', 'city', 'state', 'postal_code']:
                item[field] = next(v for k,v in item.items() if k.startswith(field))
           
            account = self.sf.find_properties_by_name(property_name)
            # print(f"account: {account}")
            result = self.sf.render_mappings('seed-salesforce-benchmarking.json.template', item)
            if account:
                # update
                self.sf.update_property_by_id(account['Id'], result)
            else:
                # create? (would we actually want to do this?)
                account = self.sf.create_property(property_name, **result)

            # assert upload
            sf_record = self.sf.find_properties_by_name(property_name)
            assert sf_record['Id'] == account['Id']

            # assert delete
            success = self.sf.delete_property_by_id(account['Id'])
            assert success

