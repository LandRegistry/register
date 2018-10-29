import json
import unittest
from unittest.mock import patch, MagicMock

from flask import g

from register.main import app
from register.utilities.data.queries import insert_item_in_transaction


class TestInsert(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    @patch('register.views.record.crypto')
    @patch('register.views.record.get_item_errors')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.insert_item_in_transaction')
    def test_insert_item(self, mock_insert, commit, start, post, mock_crypto):
        mock_crypto.validate_signature.return_value = True, ""
        post.return_value = None

        payload = {
            "item": {
                "statutory-provisions": ["Law 342"],
                "geometry": {"type": "Point", "coordinates": [1, 1]},
                "local-land-charge": 342,
                "registration-date": "2012-09-01",
                "charge-type": "Smoke Control Order",
                "originating-authority": "Dave's Charge Shop",
                "further-information": []
            },
            "item-signature": "STUFF",
            "item-hash": "totallyfakehash"
        }
        mock_insert.return_value = 17

        response = self.app.post('/record', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        print(response.data)
        self.assertEqual(response.status_code, 202)
        data = json.loads(response.data.decode())
        self.assertEqual(data['entry_number'], 17)

    @patch('register.views.record.crypto')
    @patch('register.views.record.get_item_errors')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.insert_item_in_transaction')
    def test_insert_item_badsig(self, mock_insert, commit, start, post, mock_crypto):
        mock_crypto.validate_signature.return_value = False, "Check yo sig"
        post.return_value = None

        payload = {
            "item": {
                "statutory-provisions": ["Law 342"],
                "geometry": {"type": "Point", "coordinates": [1, 1]},
                "local-land-charge": 342,
                "registration-date": "2012-09-01",
                "charge-type": "Smoke Control Order",
                "originating-authority": "Dave's Charge Shop",
                "further-information": []
            },
            "item-signature": "STUFF",
            "item-hash": "totallyfakehash"
        }
        mock_insert.return_value = 17

        response = self.app.post('/record', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        print(response.data)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(1, len(data))
        self.assertEqual({'error': 'Signature check failure', 'details': 'Check yo sig'}, data[0])

    @patch('register.views.records.get_item_errors')
    @patch('register.utilities.data.queries.start')
    @patch('register.utilities.data.queries.commit')
    @patch('register.utilities.data.queries.insert_item_in_transaction')
    def test_insert_many_items(self, mock_insert, commit, start, post):
        post.return_value = None
        payload = [
            {
                "item": {
                    "statutory-provisions": ["Law 342"],
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "local-land-charge": 343,
                    "registration-date": "2012-09-01",
                    "charge-type": "Smoke Control Order",
                    "originating-authority": "Dave's Charge Shop",
                    "further-information": []
                },
                "item-signature": "STUFF",
                "item-hash": "totallyfakehash2"
            }, {
                "item": {
                    "statutory-provisions": ["Law 342"],
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "local-land-charge": 344,
                    "registration-date": "2012-09-01",
                    "charge-type": "Smoke Control Order",
                    "originating-authority": "Dave's Charge Shop",
                    "further-information": []
                },
                "item-signature": "STUFF",
                "item-hash": "totallyfakehash"
            }, {
                "item": {
                    "statutory-provisions": ["Law 342"],
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "local-land-charge": 345,
                    "registration-date": "2012-09-01",
                    "charge-type": "Smoke Control Order",
                    "originating-authority": "Dave's Charge Shop",
                    "further-information": []
                },
                "item-signature": "STUFF",
                "item-hash": "totallyfakehash3"
            }
        ]
        mock_insert.side_effect = [20, 21, 22]
        response = self.app.post('/records', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 202)
        data = json.loads(response.data.decode())
        self.assertEqual(3, len(data))
        self.assertEqual(20, data[0]['entry-number'])
        self.assertEqual(21, data[1]['entry-number'])
        self.assertEqual(22, data[2]['entry-number'])

    def test_insert_multiple_not_a_list(self):
        payload = {"item": {"local-land-charge": "342"}, "item-signature": "STUFF", "item-hash": "totallyfakehash"}
        response = self.app.post('/records', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data.decode())
        self.assertEqual(1, len(data))
        self.assertEqual("List is invalid", data[0]['error'])

    @patch('register.app.requests.Session')
    def test_insert_multiple_list_with_rubbish(self, session):
        with app.test_request_context():
            g.session = MagicMock()
            response = MagicMock()
            response.status_code = 200
            session.return_value.post.return_value = response  # 3rd item will get this far
            payload = [
                {"item": {"obtusity": "342"}, "item-signature": "STUFF", "item-hash": "totallyfakehash"},
                {"item": {"challenge": "344"}, "item-signature": "STUFF", "item-hash": "totallyfakehash2"},
                {
                    "item": {
                        "statutory-provisions": ["Law 342"],
                        "geometry": {"type": "Point", "coordinates": [1, 1]},
                        "local-land-charge": 343,
                        "registration-date": "2012-09-01",
                        "charge-type": "Smoke Control Order",
                        "originating-authority": "Dave's Charge Shop",
                        "further-information": []
                    },
                    "item-signature": "STUFF", "item-hash": "totallyfakehash3"
                }
            ]
            response = self.app.post('/records',
                                     data=json.dumps(payload),
                                     headers={'Content-Type': 'application/json'})
            self.assertEqual(400, response.status_code)
            data = json.loads(response.data.decode())
            self.assertEqual(2, len(data))
            self.assertEqual("Item 0 is invalid", data[0]['error'])
            self.assertEqual("Item 1 is invalid", data[1]['error'])

    def test_insert_item_bad_datatype(self):
        payload = '<reallybadxml>XML Payload</reallybadxml>'
        response = self.app.post('/record', data=json.dumps(payload), headers={'Content-Type': 'text/xml'})
        self.assertEqual(response.status_code, 415)

    @patch('register.views.record.crypto')
    def test_insert_item_bad_envelope(self, mock_crypto):
        mock_crypto.validate_signature.return_value = True, ""
        payload = {
            "diametric": {"legislation": "Law 342", "originator": "place 342", "local-land-charge": "342"},
            "deduction": "STUFF",
            "cromulent": "totallyfakehash"
        }
        response = self.app.post('/record', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(1, len(data))
        self.assertEqual("Envelope is invalid", data[0]['error'])

    @patch('register.views.record.crypto')
    @patch('register.app.requests.Session')
    def test_insert_item_bad_item_key(self, session, mock_crypto):
        mock_crypto.validate_signature.return_value = True, ""
        with app.test_request_context():
            g.session = MagicMock()
            response = MagicMock()
            response.status_code = 400
            response.content = b'[{"location": "$.", "error": "too lazy"}]'
            session.return_value.post.return_value = response

            payload = {
                "item": {"local-land-charge": "Law 342", "squamous": "place 342", "elongated": "342"},
                "item-signature": "STUFF",
                "item-hash": "totallyfakehash"
            }

            response = self.app.post('/record', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data.decode())
            self.assertEqual(1, len(data))
            self.assertEqual("Item is invalid", data[0]['error'])

    @patch('register.views.record.crypto')
    def test_insert_item_bad_item(self, mock_crypto):
        mock_crypto.validate_signature.return_value = True, ""
        payload = {
            "item": {"rubose": "Law 342", "squamous": "place 342", "elongated": "342"},
            "item-signature": "STUFF",
            "item-hash": "totallyfakehash"
        }

        response = self.app.post('/record', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(1, len(data))
        self.assertEqual("Item is invalid", data[0]['error'])

    @patch('register.utilities.data.queries.read_record_by_field_value')
    @patch('register.utilities.data.queries.publish_message')
    def test_insert_item_in_transaction_not_existing(self, mock_pub, mock_get_record):
        cursor = MagicMock()
        # Fiddly: this calls two SQL reads (until we get 9.6 and its UPSERTS at least):
        cursor.fetchone.side_effect = [
            {'c': 0},
            {'entry_number': 43}
        ]
        outcome = insert_item_in_transaction(
            cursor,
            {'local-land-charge': '777666555'},
            'hashhashhash',
            'sigsigsig'
        )
        self.assertEqual(cursor.execute.call_count, 5)
        self.assertEqual(43, outcome)

    @patch('register.utilities.data.queries.read_record_by_field_value')
    @patch('register.utilities.data.queries.publish_message')
    def test_insert_item_in_transaction_existing(self, mock_pub, mock_get_record):
        cursor = MagicMock()
        # Fiddly: this calls two SQL reads (until we get 9.6 and its UPSERTS at least):
        cursor.fetchone.side_effect = [
            {'c': 1},
            {'entry_number': 43}
        ]
        outcome = insert_item_in_transaction(
            cursor,
            {'local-land-charge': '777666555'},
            'hashhashhash',
            'sigsigsig'
        )
        self.assertEqual(cursor.execute.call_count, 4)
        self.assertEqual(43, outcome)
