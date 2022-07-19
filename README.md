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
    "use_ssl": true
}
```

### Running Tests

Make sure to add and configure the SEED and Salesforce configuration files. Note that they must be named `seed-config-dev.json` and `salesforce-config-dev.json` for the tests to run correctly.

Run the tests using:

```
poetry run pytest
```

### TODO

- [ ] Create template mapping file between SEED and Salesforce
- [ ] Add in integration tests, save credentials to GitHub (look at py-seed for how to launch SEED for integration testing)
- [ ] Create background running task for syncing
- [ ] (optional) create webservice to kick off syncing.
