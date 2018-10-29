import json
from Crypto.Hash import SHA256
from base64 import b16encode


def calculate_leaf_hash(entry):
    json_string = json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    # TODO(reference implementation gets Bytes directly from Java String (So... UTF-16 or some platform default?))
    as_bytes = b'\x00' + json_string.encode('UTF-8')
    hash_bytes = SHA256.new(as_bytes).digest()
    return b16encode(hash_bytes)
