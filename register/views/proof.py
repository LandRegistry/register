from base64 import b16encode
from datetime import datetime
from flask import Blueprint, Response
from flask import current_app
from register.utilities.data.merkle_data import MerkleData
from register.exceptions import ApplicationError
from register.utilities.data.connection import start, commit
from register.utilities.merkle_tree import MerkleTree
import json

proof = Blueprint('proof', __name__)


@proof.route('/register/<proof_identifier>', methods=['GET'])
def get_register_proof(proof_identifier):
    current_app.logger.info("Get register proof")
    if proof_identifier != 'merkle:sha-256':
        current_app.logger.warning("Invalid proof identifier supplied: %s", proof_identifier)
        raise ApplicationError("Invalid proof identifier", "E400", 400)

    cursor = start()
    try:
        mtree_data = MerkleData(cursor)
        mtree = MerkleTree(mtree_data)

        result = {
            "proof-identifier": "merkle:sha-256",
            "tree-size": mtree.tree_size(),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            "root-hash": "sha-256:" + b16encode(mtree.root_hash()).decode(),
            "tree-head-signature": "TODO"  # TODO(signature)
        }
        current_app.logger.info("Returning register proof")
        return Response(json.dumps(result), mimetype='application/json')
    finally:
        commit(cursor)


@proof.route('/entry/<entry_number>/<total_entries>/<proof_identifier>', methods=['GET'])
def get_entry_proof(entry_number, total_entries, proof_identifier):
    current_app.logger.info("Get entry proof for entry %s of %s", str(entry_number), str())
    if proof_identifier != 'merkle:sha-256':
        current_app.logger.warning("Invalid proof identifier supplied: %s", proof_identifier)
        raise ApplicationError("Invalid proof identifier", "E400", 400)

    cursor = start()
    try:
        mtree_data = MerkleData(cursor)
        mtree = MerkleTree(mtree_data)
        path = mtree.entry_proof(int(entry_number), int(total_entries))

        result = {
            "proof-identifier": "merkle:sha-256",
            "entry-number": entry_number,
            "merkle-audit-path": []
        }

        for item in path:
            current_app.logger.debug("{}".format(type(item)))
            result['merkle-audit-path'].append("sha-256:" + b16encode(item).decode())

        current_app.logger.info("Return entry proof (path length %d)", len(result['merkle-audit-path']))
        return Response(json.dumps(result), mimetype='application/json')

    finally:
        commit(cursor)


@proof.route('/consistency/<total_entries_1>/<total_entries_2>/<proof_identifier>', methods=['GET'])
def get_consistency_proof(total_entries_1, total_entries_2, proof_identifier):
    current_app.logger.info("Get consistency proof for trees with sizes %s and %s",
                            str(total_entries_1),
                            str(total_entries_2))
    if proof_identifier != 'merkle:sha-256':
        current_app.logger.warning("Invalid proof identifier supplied: %s", proof_identifier)
        raise ApplicationError("Invalid proof identifier", "E400", 400)

    cursor = start()
    try:
        mtree_data = MerkleData(cursor)
        mtree = MerkleTree(mtree_data)
        nodes = mtree.consistency_proof(int(total_entries_1), int(total_entries_2))

        result = {
            "proof-identifier": "merkle:sha-256",
            "merkle-consistency-nodes": []
        }

        for item in nodes:
            current_app.logger.debug("{}".format(type(item)))
            result['merkle-consistency-nodes'].append("sha-256:" + b16encode(item).decode())

        current_app.logger.info("Return consistency proof (%d nodes)", len(result['merkle-consistency-nodes']))
        return Response(json.dumps(result), mimetype='application/json')

    finally:
        commit(cursor)


@proof.route('/records/<proof_identifier>', methods=['GET'])
def get_records_proof(proof_identifier):  # pragma: no cover
    # Marked as experimental in the spec and not implemented in the reference implementation
    current_app.logger.warning("Get records proof is not implemented")
    raise ApplicationError("Not implemented", "E501", 501)


@proof.route('/record/<total_entries>/<field_value>/<proof_identifier>', methods=['GET'])
def get_record_proof(total_entries, field_value, proof_identifier):  # pragma: no cover
    # Marked as experimental in the spec and not implemented in the reference implementation
    current_app.logger.warning("Get record proof is not implemented")
    raise ApplicationError("Not implemented", "E501", 501)
