from flask import Blueprint, current_app
from register.exceptions import ApplicationError

items = Blueprint('items', __name__)


@items.route('', methods=['GET'])
def get_items():  # pragma: no cover
    # TODO(Spec is unclear... all items, or latest versions of each? Not in reference implementation.)
    current_app.logger.warning("Get items is not implemented")
    raise ApplicationError("Not implemented", "E501", 501)
