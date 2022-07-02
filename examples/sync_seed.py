# Example to read and sync seed properties with salesforce

# ./manage.py create_test_user_json --username nicholas.long@nrel.gov --file ../py-seed/seed-config.json --pyseed

from pathlib import Path

import usaddress
import os, sys

from seed_salesforce.seed_salesforce import SeedSalesforce

seed_config = Path('seed-config-dev-local.json')
sf_config = Path('salesforce-config-dev.json')

client = SeedSalesforce.init_with_files(seed_config_file=seed_config, salesforce_config_file=sf_config)
client.set_org_by_name('nrel')
client.set_cycle_by_name('2023')

# add/get Upload to Salesforce label
upload_label = client.seed.get_or_create_label('Upload to Salesforce', color='green', show_in_list=True)
violation_label = client.seed.get_or_create_label('Violation', color='green', show_in_list=True)

# TODO: need to find a get_buildings endpoint that doesn't result in the IDs getting appended to the keys.
props = client.seed.get_buildings()
for prop in props:
    print(prop['address_line_1_9'])

# find the properties with "upload to salesforce" label
to_upload = client.seed.get_view_ids_with_label([upload_label['name']])
# the 0th element is the only label (Upload to Salesforce)
for upload_id in to_upload[0]['is_applied']:
    print(upload_id)
    # get the property from seed

    prop = client.seed.get_property(upload_id)
    print(prop)

    sf_property = client.salesforce.find_properties_by_name(prop['state']['property_name'])

    addr = usaddress.tag(prop['state']['address_line_1'])[0]

    address_str = f"{addr.get('AddressNumber', '')} {addr.get('StreetName', '')} {addr.get('StreetNamePostType', '')}"
    city = addr.get('PlaceName', prop['state'].get('city', ''))
    state = addr.get('StateName', prop['state'].get('state', ''))
    postal_code = addr.get('ZipCode', prop['state'].get('postal_code', ''))

    property_data_map = {
        'AccountNumber': '',
        'TickerSymbol': 'In Violation',
        'ShippingStreet': address_str,
        'ShippingCity': city,
        'ShippingState': state,
        'ShippingPostalCode': postal_code,
    }

    if sf_property:
        sf_prop = client.salesforce.update_property_by_id(sf_property['Id'], update_data=property_data_map)
    else:
        sf_prop = client.salesforce.create_property(prop['state']['property_name'], **property_data_map)
    print(sf_prop)

    # remove the Upload label?
