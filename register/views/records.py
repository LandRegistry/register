from flask import Blueprint, Response, request, current_app
from register.pagination import paginated_resource
from register.utilities.data.queries import read_all_records, read_records_by_attribute, insert_items
from register.utilities.validation import get_list_errors, get_item_errors
import json

records = Blueprint('records', __name__)


@records.route('', methods=['GET'])
@paginated_resource
def get_records(page):
    current_app.logger.info("Get records")
    data, count = read_all_records(page.start, page.limit)
    page.set_count(count)
    current_app.logger.info("Return %d records", len(data))
    return Response(json.dumps(data), mimetype='application/json')


@records.route('/<field_name>/<field_value>')
def get_records_by_field_value(field_name, field_value):
    current_app.logger.info("Get records by %s = %s", field_name, field_value)
    data = read_records_by_attribute(field_name, field_value)
    current_app.logger.info("Return %d records", len(data))
    return Response(json.dumps(data), mimetype='application/json')


@records.route('', methods=['POST'])
def add_items():
    # There's no POST stuff currently in the spec. This one takes a list of already minted items
    current_app.audit_logger.info("Add multiple items")
    payload = request.get_json()
    errors = []
    list_errors = get_list_errors(payload)
    if list_errors is not None:
        errors.append({
            "error": "List is invalid",
            "details": list_errors
        })
    else:
        for index, item in enumerate(payload):
            item_errors = get_item_errors(item['item'])
            if item_errors is not None:
                errors.append({
                    "error": "Item {} is invalid".format(index),
                    "details": item_errors
                })

    if len(errors) > 0:
        current_app.logger.warning("There were validation errors")
        return Response(json.dumps(errors), status=400, headers={'Content-Type': 'application/json'})

    resp = insert_items(payload)
    current_app.logger.info("Items added to register")
    return Response(json.dumps(resp), status=202)
