from flask import Blueprint, Response
from register.utilities.data.connection import start, commit
from register.app import app
from register.utilities.data.queries import count_all_records, count_entries, count_items, get_lastest_update
import json

register_blueprint = Blueprint('register', __name__)


@register_blueprint.route('', methods=['GET'])
def get_register():
    app.logger.info("Get register")
    record = json.load(open(app.config['REGISTER_RECORD']))
    cursor = start()
    try:
        response_data = {
            "domain": "TBC",
            "last-updated": get_lastest_update(cursor),
            "register-record": record,
            "total-entries": count_entries(cursor),
            "total-items": count_items(cursor),
            "total-records": count_all_records(cursor)
        }
        return Response(json.dumps(response_data), mimetype='application/json')
    finally:
        commit(cursor)
