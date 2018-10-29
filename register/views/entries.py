from flask import Blueprint, Response, current_app, request
from register.utilities.data.connection import start, commit
from register.pagination import paginated_resource
from register.utilities.data.queries import read_entries, count_entries, republish_entry
from register.exceptions import ApplicationError
import json

entries = Blueprint('entries', __name__)


@entries.route('', methods=['GET'])
@paginated_resource
def get_entries(page):
    current_app.logger.info("Get entries ")
    cursor = start()
    try:
        max_entry_number = count_entries(cursor)
        entry_list = read_entries(
            cursor, page.start, page.limit, max_entry_number)
        page.set_count(max_entry_number)
    finally:
        commit(cursor)
    current_app.logger.info("Returning %d entries", len(entry_list))
    return Response(json.dumps(entry_list), mimetype='application/json')


@entries.route('/republish', methods=['POST'])
def republish_entries():
    # Republish given entries to a given routing key
    current_app.logger.info("Republishing entries")
    payload = request.get_json()
    if 'entries' not in payload or not payload['entries']:
        raise ApplicationError(
            "Payload must contain 'entries' with a list of entries to republish", "RP400", 400)
    if 'routing_key' not in payload or not payload['routing_key']:
        raise ApplicationError(
            "Payload must contain 'routing_key' with a routing key to publish using", "RP400", 400)

    current_app.logger.info(
        "Republishing entries '%s'", payload['entries'])

    result = {"republished_entries": [], "entries_not_found": []}

    for entry_number in payload['entries']:
        if republish_entry(entry_number, payload['routing_key']):
            result['republished_entries'].append(entry_number)
        else:
            result['entries_not_found'].append(entry_number)

    if result['entries_not_found']:
        status = 404
    else:
        status = 200

    current_app.logger.info(
        "Republish finished '%s'", result)

    return Response(json.dumps(result), status=status, mimetype='application/json')
