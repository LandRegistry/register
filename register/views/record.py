import json

from flask import Blueprint, Response, request, current_app
from flask_negotiate import consumes
from register.exceptions import ApplicationError
from register.extensions import crypto
from register.utilities.data.queries import read_record_by_field_value, read_record_entries, insert_item
from register.utilities.validation import get_envelope_errors, get_item_errors

record = Blueprint('record', __name__)


@record.route('/<field_value>', methods=['GET'])
def get_record(field_value):
    current_app.logger.info("Get record by field value %s", field_value)
    result = read_record_by_field_value(field_value)
    if result is None:
        current_app.logger.warning("Record with field value %s not found", field_value)
        raise ApplicationError("Not found", "E404", 404)
    current_app.logger.info("Return record")
    return Response(json.dumps(result), mimetype='application/json')


@record.route('/<field_value>/entries', methods=['GET'])
def get_record_entries(field_value):
    current_app.logger.info("Get record entries by field value %s", field_value)
    result = read_record_entries(field_value)
    if result is None:
        current_app.logger.warning("Record with field value %s not found", field_value)
        raise ApplicationError("Not found", "E404", 404)
    current_app.logger.info("Return record entries")
    return Response(json.dumps(result), mimetype='application/json')


@record.route('', methods=['POST'])
@consumes('application/json')
def add_item():
    # There's no POST stuff currently in the spec. This one takes an already minted item
    current_app.audit_logger.info("Add record to register")
    payload = request.get_json()

    errors = []
    envelope_errors = get_envelope_errors(payload)
    if envelope_errors is not None:
        errors.append({
            "error": "Envelope is invalid",
            "details": envelope_errors
        })
    else:
        # Only check signature is envelope ok since may not have correct fields
        json_string = json.dumps(payload['item'], sort_keys=True, separators=(',', ':'))
        valid, message = crypto.validate_signature(json_string, payload['item-signature'], payload['item-hash'])
        if not valid:
            errors.append({
                "error": "Signature check failure",
                "details": message
            })

    if 'item' in payload:
        item_errors = get_item_errors(payload['item'])
        if item_errors is not None:
            errors.append({
                "error": "Item is invalid",
                "details": item_errors
            })

    if len(errors) > 0:
        current_app.logger.warning("Record failed validation")
        return Response(json.dumps(errors), status=400, headers={'Content-Type': 'application/json'})

    else:
        entry_number = insert_item(payload['item'], payload['item-hash'], payload['item-signature'])
        headers = {
            'Location': '/entry/{}'.format(entry_number)
        }
        current_app.audit_logger.info("Added new entry number %s", str(entry_number))
        return Response(json.dumps({'entry_number': entry_number}), status=202, headers=headers)
