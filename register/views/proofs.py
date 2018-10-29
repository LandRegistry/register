from flask import Blueprint, Response, current_app
import json

proofs = Blueprint('proofs', __name__)


@proofs.route('', methods=['GET'])
def get_proofs():
    current_app.logger.info("Get available proofs")
    return Response(json.dumps(['merkle:sha-256']), mimetype='application/json')
