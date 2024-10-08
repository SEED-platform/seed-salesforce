# Copyright (c) Alliance for Sustainable Energy, LLC. See also https://github.com/seed-platform/seed-salesforce/blob/develop/LICENSE.md

import random
import unittest
from pathlib import Path

from seed_salesforce.salesforce_client import SalesforceClient


class SalesforceClientTest(unittest.TestCase):
    def test_init_by_file(self):
        config_file = Path("salesforce-config-dev.json")
        sf = SalesforceClient(connection_config_filepath=config_file)
        # check if the Salesforce connection has the base_url method and that it is not None
        assert hasattr(sf.connection, "base_url")
        # print(f"sf connection: {sf.connection.base_url}")
        assert sf.connection.base_url is not None


class SalesforceIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path("tests/output")
        if not self.output_dir.exists():
            self.output_dir.mkdir()

        # create the connection to salesforce.
        # These tests run against a development version of Salesforce
        config_file = Path("salesforce-config-dev.json")
        self.sf = SalesforceClient(connection_config_filepath=config_file)

        self.test_org = "New Test Account"
        self.test_email = "a-user@somecompany.com"
        self.test_benchmark_name = "Example Benchmarking"
        self.account_record_type = None
        self.contact_record_type = "0124p000000ZwnEAAS"

        return super().setUp()

    # @pytest.mark.skip(reason="Need to confirm that this is a valid test")
    def test_search_and_create_and_delete_account(self):
        r = random.randrange(1, 5000, 2)
        test_account_name = f"Scrumptious Ice Cream{r}"
        account = self.sf.find_account_by_name(test_account_name)
        # The first time should not have any results
        assert not account

        details = {
            "Type": "Ice Cream Shop",
            "Phone": "555-867-5309",
            "Website": "http://www.scrumptiousco.com",
        }
        if self.account_record_type:
            details["RecordTypeID"] = self.account_record_type

        account = self.sf.create_account(test_account_name, **details)
        account_id = account["Id"]
        # print(f"ACCOUNT ID: {account_id}")
        assert account["Name"] == test_account_name
        assert account["Type"] == "Ice Cream Shop"
        assert account_id is not None

        # Find the record
        account = self.sf.find_account_by_name(test_account_name)
        assert account["Id"] == account_id

        # now delete it to cleanup
        success = self.sf.delete_account_by_id(account_id)
        assert success

    # @pytest.mark.skip(reason="Need to confirm that this is a valid test")
    def test_update_contact_and_account(self):
        r = random.randrange(1, 5000, 2)
        test_account_name = "A Fake Account" + str(r)
        details = {
            "Type": "Office",
            "Phone": "555-867-5309",
            "Website": "http://www.scrumptiousco.com",
        }
        if self.account_record_type:
            details["RecordTypeID"] = self.account_record_type

        account = self.sf.create_account(test_account_name, **details)
        account_id = account["Id"]

        success = self.sf.update_account_by_id(
            account_id,
            {
                "Phone": "444-444-4444",
                "Website": "http://www.UpdatedWebsite.com",
            },
        )
        # this returns a 204 but seems to do so regardless of whether property exists
        assert success

        # contacts
        # create contact (associated with account)
        details = {
            "AccountId": account_id,
            "LastName": "Richard Hendrick" + str(r),
        }
        if self.contact_record_type:
            details["RecordTypeID"] = self.contact_record_type

        self.sf.create_contact("user" + str(r) + "@company.com", **details)
        # retrieve contact
        contact = self.sf.find_contact_by_email("user" + str(r) + "@company.com")
        assert contact["AccountId"] == account_id

        # update contact (can't change email)
        details = {
            "AccountId": account_id,
            "LastName": "Russ Hanneman" + str(r),
        }
        self.sf.create_or_update_contact_on_account("user" + str(r) + "@company.com", **details)
        assert contact["AccountId"] == account_id

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
        print(" ...get first benchmark (to get an ID)...")
        benchmark = self.sf.get_first_benchmark()
        print(f" Benchmark: {benchmark}")
        assert benchmark is not None
        benchmark_id = benchmark["Id"]
        salesforce_benchmark_id = benchmark["Salesforce_Benchmark_ID__c"]

        # can you retrieve by "Salesforce Benchmark ID" custom field?
        print(" ...retrieving benchmark by Salesforce Benchmark ID...")
        bench_by_custom_id = self.sf.get_benchmark_by_custom_id(salesforce_benchmark_id)
        print(f" benchmark by custom id: {bench_by_custom_id}")
        assert bench_by_custom_id["Id"] == benchmark_id

        # can you update a benchmark field?
        print(" ...updating benchmark...")
        # TODO: again assuming this field exists...it might not?
        energy_star_score = benchmark["ENERGY_STAR_Score__c"]
        new_energy_star_score = 20
        args = {"ENERGY_STAR_Score__c": new_energy_star_score}
        bench_updated = self.sf.update_benchmark(salesforce_benchmark_id, **args)
        print(f"benchmark updated: {bench_updated}")

        # retrieve again to see if it was updated
        bench2 = self.sf.get_benchmark_by_custom_id(salesforce_benchmark_id)
        assert bench2["ENERGY_STAR_Score__c"] == new_energy_star_score

        # restore value
        args["ENERGY_STAR_Score__c"] = energy_star_score
        self.sf.update_benchmark(salesforce_benchmark_id, **args)
