from register.main import app
from register.exceptions import ApplicationError
from unittest.mock import patch, MagicMock
import unittest
from datetime import datetime


class TestHealth(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_health(self):
        self.assertEqual((self.app.get('/health')).status_code, 200)

    @patch("register.dependencies.postgres.psycopg2")
    @patch('register.app.requests.Session')
    def test_health_cascade(self, requests, pg):
        response = MagicMock()
        response.status_code = 200
        response.headers = {'content-type': 'application/unit+test'}
        response.json.return_value = {}
        requests.return_value.get.return_value = response
        pg.connect.return_value.cursor.return_value.fetchone.return_value = [datetime.now()]
        response = self.app.get('/health/cascade/4')
        self.assertEqual(response.status_code, 200)

    @patch("register.views.general.postgres")
    @patch('register.app.requests.Session')
    def test_health_cascade_no_postgres(self, requests, pg):
        pg.get_current_timestamp.side_effect = ApplicationError("blah", 400)
        response = self.app.get('/health/cascade/4')
        self.assertEqual(response.status_code, 500)
