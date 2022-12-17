## SEED Salesforce Connection

The SEED Salesforce connection enables data exchange between a SEED instance and a Salesforce instance.

### Getting Started

To get started, you will need to checkout py-seed (with the branch `add-seed-helpers`) and place the project at the same level as this project. For example:

```
cd ..
git clone git@github.com:SEED-platform/py-seed.git
git checkout add-seed-helpers
```

Then install the poetry-based dependencies. Note that installing a package from GitHub through poetry can cause some issues with updating, therefore, it is easiest (for now) to clone the dependencies manually.

```
pip install poetry
poetry install
```

### Configuring

Both SEED and Salesforce configuration files are needed for this library to function correctly.

#### Salesforce

Copy `salesforce-config-example.json` to `salesforce-config-dev.json` and fill
in with the correct credentials. The format of the Salesforce should contain the following:

```
{
    "instance": "https://<url>.lightning.force.com",
    "username": "user@company.com",
    "password": "secure-password",
    "security_token": "secure-token"
}
```

**IMPORTANT:** if you are connecting to a sandbox Salesforce environment, make sure to add "domain": "test" to the `salesforce-config-dev.json` file or authentication will fail.

#### SEED

Copy `seed-config-example.json` to `seed-config-dev.json` and fill
in with the correct credentials. The format of the SEED configuration should contain the following:

```
{
    "name": "seed_api_test",
    "base_url": "https://dev1.seed-platform.org",
    "username": "user@company.com",
    "api_key": "secure-key",
    "port": 443,
    "use_ssl": true,
    "seed_org_name": "seed-org",
    "indication_label": "Add to Salesforce",
    "violation_label": "Violation - Insufficient Data",
    "complied_label": "Complied",
    "last_update_timestamp": "2001-01-01 12:00:00.000-07:00"
}
```

- `indication_label`: the label text that identifies a record that should be added to Salesforce
- `violation_label`: the label text that identifies an incomplete/erroneous record that should not be added to Salesforce
- `complied_label`: the label text that identifies a compliant record
- `last_update_timestamp`: the last timestamp that the SEED-to-Salesforce workflow was ran, in format: '%Y-%m-%d %H:%M:%S.%f%z'

### Running Tests

Make sure to add and configure the SEED and Salesforce configuration files. Note that they must be named `seed-config-dev-local.json` and `salesforce-config-dev.json` for the tests to run correctly.

Run the tests using:

```
poetry run pytest
```

### TODO

- [ ] Create template mapping file between SEED and Salesforce
- [ ] Add in integration tests, save credentials to GitHub (look at py-seed for how to launch SEED for integration testing)
- [ ] Create background running task for syncing
- [ ] (optional) create webservice to kick off syncing.
