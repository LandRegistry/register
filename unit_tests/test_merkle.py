import unittest
from unittest.mock import MagicMock
from register.utilities.data.merkle_data import MerkleData
from register.main import app
from register.utilities.data.empty_entry import create_empty_entry
from register.utilities.leaf_hash import calculate_leaf_hash


class TestMerkle(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_leaf_hash_per_spec(self):
        # Again, test data extracted from the GDS implementation
        entry = {
            "entry-number": "1",
            "entry-timestamp": "2017-01-31T14:39:05Z",
            "item-hash": "sha-256:d40c2859cb02be9e2dfb534e2bb4b322c864b3c5cfe60b544c4d77eaa61fd86d",
            "key": "1"
        }
        h = calculate_leaf_hash(entry)
        self.assertEqual(h.decode(), 'AAB9FF7666FFB2B217DA6BF40BA1B8EA7B73EF2A911FA6494A26EDB5F1C554BF')

    def test_merkle_data_class(self):
        mock_cursor = MagicMock()
        test_this = MerkleData(mock_cursor)

        mock_cursor.fetchone.return_value = {'entry_hash': 'ENTRYHASHISALIE'}
        self.assertEqual('ENTRYHASHISALIE', test_this.leaf_hash(17))

        mock_cursor.fetchone.return_value = {'branch_hash': 'BRANCHHASHISFAKE'}
        self.assertEqual('BRANCHHASHISFAKE', test_this.branch_hash(10, 100))
        # TODO(assert the parameters are calculated correctly?)

    def test_empty_entry(self):
        entry = create_empty_entry(127)
        self.assertEqual(entry['entry-number'], 127)
        self.assertIsNone(entry['item-hash'])

    def test_empty_leaf_hash(self):
        leaf_hash = calculate_leaf_hash(create_empty_entry(698)).decode()
        self.assertEqual(leaf_hash, 'F0C3DCD45728134CF63D4C59B9BA442D6056E24B46EBF76E9F6648E8E7068E3B')
