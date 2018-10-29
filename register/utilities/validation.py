from jsonschema import Draft4Validator
from register.app import app
from flask import g
import json

RECORD_SCHEMA = {
    "type": "object",
    "properties": {
        "item": {"type": "object"},
        "item-hash": {"type": "string"},
        "item-signature": {"type": "string"}
    },
    "additionalProperties": False,
    "required": ["item", "item-hash", "item-signature"]
}

LIST_OF_RECORDS_SCHEMA = {
    "type": "array",
    "items": RECORD_SCHEMA
}


def _check_for_errors(data, schema):
    validator = Draft4Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        # TODO(do we want to nicify these?)
        path = "$"
        while len(error.path) > 0:
            item = error.path.popleft()
            if isinstance(item, int):  # This is an assumption!
                path += "[" + str(item) + "]"
            else:
                path += "." + item
        if path == '$':
            path = '$.'

        app.logger.warning("Validation error at {} Message: {}".format(path, error.message))
        errors.append({
            "error_message": error.message,
            "location": path
        })

    return errors if len(errors) > 0 else None


def get_envelope_errors(data):
    app.logger.info("Validate envelope")
    return _check_for_errors(data, RECORD_SCHEMA)


def get_item_errors(data):
    app.logger.info("Validate item")
    if app.config['REGISTER_KEY_FIELD'] not in data:
        return [{
            'location': '$.',
            'error': 'Key field ({}) is missing'.format(app.config['REGISTER_KEY_FIELD'])
        }]

    errors = None

    validation_uri = "{}/{}".format(app.config['VALIDATION_BASE_URI'],
                                    app.config['VALIDATION_ENDPOINT'])
    if validation_uri is not None:
        app.logger.info("Call validation-api")
        response = g.requests.post(validation_uri, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            app.logger.warning("Item validation failed")
            errors = json.loads(response.content.decode())
        else:
            app.logger.info("Item validated successfully")
    else:
        app.logger.warning("No validation api configured")
    return errors


def get_list_errors(data):
    return _check_for_errors(data, LIST_OF_RECORDS_SCHEMA)
