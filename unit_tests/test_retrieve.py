import datetime
import json
import unittest
from unittest.mock import MagicMock, patch

from register.main import app
from register.utilities.data.queries import count_entries, count_items, count_all_records, get_lastest_update

entry_row = {
    "entry_number": 1,
    "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 123654),
    "item_hash": "sha-256:7f9c9e31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
    "key": "1",
    "item_signature": "SIGNATURE"
}

item_row = {
    "item": {"local-land-charge": "LC001234", "originator": "Generic Local Authority"}
}

entry_rows = [
    {
        "entry_number": 2,
        "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 123654),
        "item_hash": "sha-256:7f9c9e31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
        "key": "1",
        "item_signature": "SIGNATURE"
    },
    {
        "entry_number": 1,
        "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 999888),
        "item_hash": "sha-256:aaaccd31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
        "key": "2",
        "item_signature": "SIGNATURE"
    }
]

entry_rows_gap = [
    {
        "entry_number": 3,
        "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 123654),
        "item_hash": "sha-256:7f9c9e31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
        "key": "1",
        "item_signature": "SIGNATURE"
    },
    {
        "entry_number": 1,
        "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 999888),
        "item_hash": "sha-256:aaaccd31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
        "key": "2",
        "item_signature": "SIGNATURE"
    }
]

record_row = {
    "entry_number": 1,
    "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 123654),
    "item_hash": "sha-256:7f9c9e31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
    "key": "1",
    "item_signature": "SIGNATURE",
    "item": {"local-land-charge": "LC001234", "originator": "Generic Local Authority"}
}

record_rows = [
    {
        "entry_number": 1,
        "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 123654),
        "item_hash": "sha-256:7f9c9e31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
        "key": "1",
        "item_signature": "SIGNATURE",
        "item": {"local-land-charge": "LC001234", "originator": "Generic Local Authority"}
    },
    {
        "entry_number": 2,
        "entry_timestamp": datetime.datetime(2017, 1, 30, 12, 32, 45, 999888),
        "item_hash": "sha-256:aaaccd31ac8256ca2f258583df262dbc7d6f68f2a03043d5c99a4ae5a7396ce9",
        "key": "2",
        "item_signature": "SIGNATURE",
        "item": {"local-land-charge": "LC001234", "originator": "Generic Local Authority"}
    }
]


class TestRetrieve(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.count_entries')
    def test_get_entry(self, count, mock_start, mock_commit):
        mock_start.return_value.fetchone.return_value = entry_row
        count.return_value = 100
        response = self.app.get("/entry/1")
        data = json.loads(response.data.decode())
        self.assertEqual(str(entry_row['entry_number']), data['entry-number'])
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.count_entries')
    def test_get_entry_404(self, count, mock_start, mock_commit):
        count.return_value = 100
        mock_start.return_value.fetchone.return_value = None
        response = self.app.get("/entry/150")
        self.assertEqual(response.status_code, 404)

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.count_entries')
    def test_get_entry_gap(self, count, mock_start, mock_commit):
        count.return_value = 100
        mock_start.return_value.fetchone.return_value = None
        response = self.app.get("/entry/50")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['entry-number'], '50')
        self.assertIsNone(data['item-hash'])

    @patch('register.views.entries.count_entries')
    @patch('register.views.entries.commit')
    @patch('register.views.entries.start')
    def test_get_entries(self, mock_start, mock_commit, mock_count):
        mock_start.return_value.fetchall.return_value = entry_rows
        mock_count.return_value = len(entry_rows)
        response = self.app.get("/entries")
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(entry_rows))
        mock_commit.assert_called_once()
        self.assertEqual(data[0]['entry-number'], 2)
        self.assertEqual(data[1]['entry-number'], 1)

    @patch('register.views.entries.count_entries')
    @patch('register.views.entries.commit')
    @patch('register.views.entries.start')
    def test_get_entries_gap(self, mock_start, mock_commit, mock_count):
        mock_start.return_value.fetchall.return_value = entry_rows_gap
        mock_count.return_value = len(entry_rows_gap) + 1
        response = self.app.get("/entries")
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(entry_rows_gap) + 1)
        self.assertEqual(data[0]['entry-number'], 3)
        self.assertEqual(data[1]['entry-number'], 2)
        self.assertEqual(data[2]['entry-number'], 1)
        mock_commit.assert_called_once()

    @patch('register.utilities.data.queries.count_entries')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.publish_message')
    def test_republish_entries_ok(self, mock_publish, mock_start, mock_commit, mock_count):
        mock_count.return_value = 100
        mock_start.return_value.fetchone.side_effect = [
            record_rows[1], record_rows[0]]
        response = self.app.post("/entries/republish",
                                 data=json.dumps(
                                     {"entries": [2], "routing_key": "key"}),
                                 headers={"Content-type": "application/json"})
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()
        self.assertEqual(
            data, {"republished_entries": [2], "entries_not_found": []})

    @patch('register.utilities.data.queries.count_entries')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.publish_message')
    def test_republish_entries_missing(self, mock_publish, mock_start, mock_commit, mock_count):
        mock_count.return_value = 100
        mock_start.return_value.fetchone.side_effect = [None]
        response = self.app.post("/entries/republish",
                                 data=json.dumps(
                                     {"entries": [2], "routing_key": "key"}),
                                 headers={"Content-type": "application/json"})
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()
        self.assertEqual(
            data, {"republished_entries": [2], "entries_not_found": []})

    @patch('register.utilities.data.queries.count_entries')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.publish_message')
    def test_republish_entries_ok_multi(self, mock_publish, mock_start, mock_commit, mock_count):
        mock_count.return_value = 100
        mock_start.return_value.fetchone.side_effect = [
            record_rows[1], record_rows[0], record_rows[1], record_rows[0]]
        response = self.app.post("/entries/republish",
                                 data=json.dumps(
                                     {"entries": [1, 2], "routing_key": "key"}),
                                 headers={"Content-type": "application/json"})
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_commit.call_count, 2)
        self.assertEqual(
            data, {"republished_entries": [1, 2], "entries_not_found": []})

    @patch('register.utilities.data.queries.count_entries')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.publish_message')
    def test_republish_entries_over_max(self, mock_publish, mock_start, mock_commit, mock_count):
        mock_count.return_value = 1
        mock_start.return_value.fetchone.side_effect = [
            record_rows[1], record_rows[0], record_rows[1], record_rows[0]]
        response = self.app.post("/entries/republish",
                                 data=json.dumps(
                                     {"entries": [1, 2], "routing_key": "key"}),
                                 headers={"Content-type": "application/json"})
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 404)
        self.assertEqual(mock_commit.call_count, 2)
        self.assertEqual(
            data, {"republished_entries": [1], "entries_not_found": [2]})

    def test_republish_no_entries(self):
        response = self.app.post("/entries/republish",
                                 data=json.dumps(
                                     {"routing_key": "key"}),
                                 headers={"Content-type": "application/json"})
        self.assertEqual(response.status_code, 400)

    def test_republish_no_routing_key(self):
        response = self.app.post("/entries/republish",
                                 data=json.dumps(
                                     {"entries": [1, 2]}),
                                 headers={"Content-type": "application/json"})
        self.assertEqual(response.status_code, 400)

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_item(self, mock_start, mock_commit):
        mock_start.return_value.fetchone.return_value = item_row
        response = self.app.get(
            "/item/sha-256:blahblahfakehashnotevenrealistic")
        data = json.loads(response.data.decode())
        self.assertEqual("Generic Local Authority", data['originator'])
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_item_404(self, mock_start, mock_commit):
        mock_start.return_value.fetchone.return_value = None
        response = self.app.get(
            "/item/sha-256:blahblahfakehashnotevenrealistic")
        self.assertEqual(response.status_code, 404)

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_item_entries(self, mock_start, mock_commit):
        mock_start.return_value.fetchall.return_value = entry_rows
        response = self.app.get(
            "/item/sha-256:blahblahfakehashnotevenrealistic/entries")
        data = json.loads(response.data.decode())
        self.assertEqual(len(data), len(entry_rows))
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_item_entries_404(self, mock_start, mock_commit):
        mock_start.return_value.fetchall.return_value = []
        response = self.app.get(
            "/item/sha-256:blahblahfakehashnotevenrealistic/entries")
        self.assertEqual(response.status_code, 404)

    @patch('register.views.proof.MerkleData')
    @patch('register.views.proof.commit')
    @patch('register.views.proof.start')
    def test_get_register_proof_empty(self, mock_start, mock_commit, mock_treedata):
        leaf_hash = '7fa394d1c4a1a9d393147e37ce536a66c539c8da326932e87a9260d98f4678dc'
        branch_hash = '7fa394d1c4a1a9d393147e37ce536a66c539c8da326932e87a9260d98f4678dc'
        mock_treedata.return_value.leaf_hash.return_value = leaf_hash
        mock_treedata.return_value.branch_hash.return_value = branch_hash
        mock_treedata.return_value.leaf_count.return_value = 0
        response = self.app.get('/proof/register/merkle:sha-256')
        data = json.loads(response.data.decode())
        self.assertEqual(
            'sha-256:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855', data['root-hash'])
        self.assertEqual(0, data['tree-size'])

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_register_proof_bad(self, mock_start, mock_commit):
        response = self.app.get('/proof/register/capriciousness:sha-256')
        self.assertEqual(response.status_code, 400)

    @patch('register.views.proof.MerkleData')
    @patch('register.views.proof.commit')
    @patch('register.views.proof.start')
    def test_get_register_proof_nonempty(self, mock_start, mock_commit, mock_treedata):
        mock_treedata.return_value.leaf_hash = self.fake_leaf_hash
        mock_treedata.return_value.branch_hash.return_value = None
        mock_treedata.return_value.leaf_count.return_value = 4
        response = self.app.get('/proof/register/merkle:sha-256')
        data = json.loads(response.data.decode())
        # Based on the hashes in fake_leaf_hash, this is the correct MTH
        # according to GDS' reference implementation
        self.assertEqual(
            'sha-256:E1CEEBC7BE6FA1DE812C7C2B08440BAF65317978E125C35FFBE93F6613BCABA7', data['root-hash'])
        self.assertEqual(4, data['tree-size'])

    @patch('register.views.proof.MerkleData')
    @patch('register.views.proof.commit')
    @patch('register.views.proof.start')
    def test_get_entry_proof_nonempty(self, mock_start, mock_commit, mock_treedata):
        mock_treedata.return_value.leaf_hash = self.fake_leaf_hash
        mock_treedata.return_value.branch_hash.return_value = None
        mock_treedata.return_value.leaf_count.return_value = 4
        response = self.app.get('/proof/entry/1/4/merkle:sha-256')
        data = json.loads(response.data.decode())
        # Based on the hashes in fake_leaf_hash, this is the correct proof
        # according to GDS' reference implementation
        self.assertEqual(len(data['merkle-audit-path']), 2)
        self.assertEqual(data['merkle-audit-path'][0],
                         'sha-256:5D971F9169038C7DC9746A8F61C77B68AEA7BC7F458C81D410B5BE70F2FE0F01')
        self.assertEqual(data['merkle-audit-path'][1],
                         'sha-256:4846755F2F9A7649E571D4340421970B1324A0ABD2D27D650F3A8DB9DDFEA003')

    @patch('register.views.proof.MerkleData')
    @patch('register.views.proof.commit')
    @patch('register.views.proof.start')
    def test_get_register_consistency_nonempty(self, mock_start, mock_commit, mock_treedata):
        mock_treedata.return_value.leaf_hash = self.fake_leaf_hash
        mock_treedata.return_value.branch_hash.return_value = None
        mock_treedata.return_value.leaf_count.return_value = 4
        response = self.app.get('/proof/consistency/2/4/merkle:sha-256')
        data = json.loads(response.data.decode())
        # Based on the hashes in fake_leaf_hash, this is the correct proof
        # according to GDS' reference implementation
        self.assertEqual(len(data['merkle-consistency-nodes']), 1)
        self.assertEqual(data['merkle-consistency-nodes'][0],
                         'sha-256:4846755F2F9A7649E571D4340421970B1324A0ABD2D27D650F3A8DB9DDFEA003')

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_record(self, mock_start, mock_commit):
        mock_start.return_value.fetchone.return_value = record_row
        response = self.app.get("/record/1")
        data = json.loads(response.data.decode())
        self.assertEqual(record_row['entry_number'], data['entry-number'])
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_record_404(self, mock_start, mock_commit):
        mock_start.return_value.fetchone.return_value = None
        response = self.app.get("/record/1")
        self.assertEqual(response.status_code, 404)

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_record_entries(self, mock_start, mock_commit):
        mock_start.return_value.fetchall.return_value = entry_rows
        response = self.app.get("/record/1/entries")
        data = json.loads(response.data.decode())
        self.assertEqual(len(data), len(entry_rows))
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_record_entries_404(self, mock_start, mock_commit):
        mock_start.return_value.fetchall.return_value = []
        response = self.app.get("/record/1/entries")
        self.assertEqual(response.status_code, 404)

    @patch('register.utilities.data.queries.count_all_records')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_records(self, mock_start, mock_commit, mock_count):
        mock_start.return_value.fetchall.return_value = record_rows
        mock_count.return_value = len(entry_rows)
        response = self.app.get("/records")
        data = json.loads(response.data.decode())
        self.assertEqual(len(data), len(record_rows))
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    @patch('register.views.register.start')
    @patch('register.views.register.commit')
    @patch('register.views.register.get_lastest_update')
    def test_get_register(self, update, commit, start):
        start.return_value.fetchone.return_value = {'count': 4}
        update.return_value = '2017-01-01 12:13:14.555666'
        response = self.app.get("/register")
        data = json.loads(response.data.decode())
        self.assertEqual(data['total-entries'], 4)
        self.assertEqual(data['total-items'], 4)

    def fake_leaf_hash(self, entry_number):
        # I created a four entry register in the OpenRegister-Java implementation, extracted the leaf hashes to
        # create this list. I then used the proof roots of that application to
        # create the test bits here.
        return [
            'aab9ff7666ffb2b217da6bf40ba1b8ea7b73ef2a911fa6494a26edb5f1c554bf',
            '5d971f9169038c7dc9746a8f61c77b68aea7bc7f458c81d410b5be70f2fe0f01',
            '4bc8aa003d3d39f6a395e0a33b2a96a835db77a2d22e31a410fd0ad2f2feb950',
            'fcd3061623c0409a783bb57d9768737f0a51eaa301f4ba57644366622cfa38a0'
        ][entry_number - 1]

    def test_count_entries(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {'count': 4}
        i = count_entries(cursor)
        self.assertEqual(i, 4)

    def test_count_records(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {'count': 4}
        i = count_all_records(cursor)
        self.assertEqual(i, 4)

    def test_count_items(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {'count': 4}
        i = count_items(cursor)
        self.assertEqual(i, 4)

    def test_latest_update(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            'time': datetime.datetime(2011, 1, 1, 11, 11, 11, 111111)}
        i = get_lastest_update(cursor)
        self.assertEqual(i, "2011-01-01 11:11:11.111111")

    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.start')
    def test_get_records_by_attribute(self, mock_start, mock_commit):
        mock_start.return_value.fetchall.return_value = record_rows
        response = self.app.get("/records/attribute/value")
        data = json.loads(response.data.decode())
        self.assertEqual(len(data), len(record_rows))
        self.assertEqual(response.status_code, 200)
        mock_commit.assert_called_once()

    def test_get_available_proofs(self):
        response = self.app.get('/proofs')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertGreaterEqual(1, len(data))
        self.assertEqual(data[0], 'merkle:sha-256')

    def test_request_dodgy_register_proof(self):
        response = self.app.get('/proof/register/sparkling:md5')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['error_message'], "Invalid proof identifier")

    def test_request_dodgy_audit_path(self):
        response = self.app.get('/proof/entry/7/8/gilded:sha256')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['error_message'], "Invalid proof identifier")

    def test_request_dodgy_consistency_proof(self):
        response = self.app.get('/proof/consistency/4/6/ambitious:pbkdf')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['error_message'], "Invalid proof identifier")
