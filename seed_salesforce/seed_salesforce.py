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


class SeedSalesforce(object):
    def __init__(self, seed_client: SeedClient = None, salesforce_client: SalesforceClient = None):
        self.seed = seed_client
        self.salesforce = salesforce_client

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

        return SeedSalesforce(seed_client, sf_client)

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
            org_name (str): Name of the organizaiton to use
        """
        if self.seed.get_org_by_name(org_name, set_org_id=True):
            return True
        else:
            raise Exception(f'Unable to set the org to {org_name}')

    def sync_properties_with_salesforce(self):
        print("doing something here")

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
