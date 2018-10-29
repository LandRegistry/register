from flask import Blueprint, Response
from register.app import app
from register.exceptions import ApplicationError
from register.utilities.data.queries import read_item, read_item_entries
import json

item = Blueprint('item', __name__)


@item.route('/<item_hash>', methods=['GET'])
def get_item(item_hash):
    app.logger.info("Get item %s", item_hash)
    item_data = read_item(item_hash)
    if item_data is None:
        app.logger.warning("Item %s not found", item_hash)
        raise ApplicationError("Not found", "E404", 404)
    app.logger.info("Returning item")
    return Response(json.dumps(item_data), status=200, mimetype='application/json')


@item.route('/<item_hash>/entries', methods=['GET'])
def get_item_entries(item_hash):
    app.logger.info("Get item entries %s", item_hash)
    item_data = read_item_entries(item_hash)
    if item_data is None:
        app.logger.warning("Item %s not found", item_hash)
        raise ApplicationError("Not found", "E404", 404)
    app.logger.info("Returning item entries")
    return Response(json.dumps(item_data), status=200, mimetype='application/json')
