import unittest
from flask import g
from register import cryptography
from register.main import app


test_payload = '{"thing": "ame"}'
test_sig = "rs256:P86f7Fp6txRXWz6kH08NR5hJm7dGP18KFIq6ujB9t8ZaaHLVMv8NXw/X7yc73sNGBvXu3YMancCu609ihgfuF5whWiZWtl" + \
           "kgAaFhLsufd1sW4aacUaq00iX70B2+qSN8GMDnnI9BeYqH2m9/GXcHtOuyCkzjIHJtKweGjUGwZ+UEG8RZ386UwXYUC1lUgv8lXI" + \
           "j68EOUG8lln0roCYjrr1EhqByEp/TLBxO1eSp4THgHNUp5jnkTf6a2Zt6RvYgrByHDM5oRzMw3BAxqxRKww8tAujf/JHCQFWKXqa" + \
           "BJ8ogp9vvSKCOgK2nQe0zxNzHJNGLTjlKyqNmu/Y2J+conDA=="
test_hash = "sha-256:8106d113532d3af2a9472725509137bf504ad9f13a287ee27eec3fb754fb70cb"


class TestValidate(unittest.TestCase):

    def setUp(self):
        self.cypto = cryptography.CryptographicSigning()

    def test_invalid_hash(self):
        with app.test_request_context():
            g.trace_id = 'test'
            self.assertEqual(self.cypto.validate_signature(test_payload, test_sig, "NOTAHASH"),
                             (False, "Invalid hash string 'NOTAHASH'."))

    def test_invalid_sig(self):
        with app.test_request_context():
            g.trace_id = 'test'
            self.assertEqual(self.cypto.validate_signature(test_payload, "NOTASIG", test_hash),
                             (False, "Invalid signature string 'NOTASIG'."))

    def test_no_hash_match(self):
        with app.test_request_context():
            g.trace_id = 'test'
            self.assertEqual(self.cypto.validate_signature(test_payload, test_sig, "sha-256:MADEUP"),
                             (False, "Supplied hash does not match calculated hash."))

    def test_match(self):
        with app.test_request_context():
            g.trace_id = 'test'
            self.assertEqual(self.cypto.validate_signature(test_payload, test_sig, test_hash),
                             (True, "Signature and payload match."))

    def test_no_match(self):
        with app.test_request_context():
            g.trace_id = 'test'
            self.assertEqual(self.cypto.validate_signature(test_payload, test_sig.replace('0', '2'), test_hash),
                             (False, 'Signature and payload do not match.'))
