from flask import Blueprint, Response, current_app
from register.exceptions import ApplicationError
from register.utilities.data.queries import read_entry
import json

entry = Blueprint('entry', __name__)


@entry.route("/<entry_number>", methods=['GET'])
def get_entry(entry_number):
    current_app.logger.info("Get entry %s", entry_number)
    register_entry = read_entry(entry_number)
    if register_entry is None:
        current_app.logger.warning("Entry %s not found", entry_number)
        raise ApplicationError("Not found", "E404", 404)

    current_app.logger.info("Returning entry")
    return Response(json.dumps(register_entry), mimetype='application/json')
