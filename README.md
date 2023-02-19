## SEED Salesforce Connection

The SEED Salesforce connection enables data exchange between a SEED instance and a Salesforce instance.

### Getting Started

Clone this repository, then install the poetry-based dependencies.

```
pip install poetry
poetry install
```

### Configuring

The Salesforce configuration file is needed for this library to function correctly.

#### Salesforce

Copy `salesforce-config-example.json` to `salesforce-config-dev.json` and fill
in with the correct credentials. The format of the Salesforce should contain the following:

```
{
    "instance": "https://<url>.lightning.force.com",
    "username": "user@company.com",
    "password": "secure-password",
    "security_token": "secure-token"
    "domain": ""
}
```

**IMPORTANT:** If you are connecting to a sandbox Salesforce environment, make sure to add "domain": "test" to the `salesforce-config-dev.json` file or authentication will fail.

### Running Tests

Make sure to add and configure the Salesforce configuration file. Note that it must be named `salesforce-config-dev.json` for the tests to run correctly.

Run the tests using:

```
poetry run pytest
```
