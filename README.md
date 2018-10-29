# Register
Thu 25 May 2017 11:01:30 BST

This repository contains the register application.

This repository contains a flask application structured in the way that all
Land Registry flask APIs should be structured going forwards.

The purpose of this application is to maintain and manage the register data store.

## Unit tests

The unit tests are contained in the unit_tests folder. [Pytest](http://docs.pytest.org/en/latest/) is used for unit testing. 

To run the unit tests if you are using the common dev-env use the following command:

```bash
docker-compose exec register make unittest
or, using the alias
unit-test register
```

or

```bash
docker-compose exec register make report="true" unittest
or, using the alias
unit-test register -r
```

# Linting

Linting is performed with [Flake8](http://flake8.pycqa.org/en/latest/). To run linting:
```
docker-compose exec register make lint
```

## Endpoints

This application is documented in documentation/swagger.json

# Naming

For reasons of compliance, the actual name of this module is register-api, the "actual_name" file will cause the RPM to built with this name and it's also the name the service will run under and the folder it will be in when deployed to a server.
