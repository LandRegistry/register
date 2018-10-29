from register.main import app
from register.utilities.item_helper import get_action_type, get_item_changes
import unittest


def get_item():
    return {
        'field1': 'value1',
        'field2': 'value2'
    }


def get_existing_item():
    return {
        'field1': 'value3',
        'field2': 'value4'
    }


class TestItemHelper(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_get_action_type_new(self):
        existing_item = None
        action_type = get_action_type(existing_item)
        self.assertEqual(action_type, 'NEW')

    def test_get_action_type_updated(self):
        existing_item = {'local-land-charge': 1}
        action_type = get_action_type(existing_item)
        self.assertEqual(action_type, 'UPDATED')

    def test_get_item_changes_same_fields_different_values(self):
        item = get_item()
        existing_item = get_existing_item()
        expected_item_changes = {
            'field1': {
                'old': existing_item['field1'],
                'new': item['field1']
            },
            'field2': {
                'old': existing_item['field2'],
                'new': item['field2']
            }
        }
        item_changes = get_item_changes(item, existing_item)
        self.assertEqual(item_changes, expected_item_changes)

    def test_get_item_changes_field_removed(self):
        item = get_item()
        existing_item = get_existing_item()
        item.pop('field1', None)
        expected_item_changes = {
            'field1': {
                'old': existing_item['field1'],
                'new': None
            },
            'field2': {
                'old': existing_item['field2'],
                'new': item['field2']
            }
        }
        item_changes = get_item_changes(item, existing_item)
        self.assertEqual(item_changes, expected_item_changes)

    def test_get_item_changes_field_added(self):
        item = get_item()
        existing_item = get_existing_item()
        item['field3'] = 'value5'
        expected_item_changes = {
            'field1': {
                'old': existing_item['field1'],
                'new': item['field1']
            },
            'field2': {
                'old': existing_item['field2'],
                'new': item['field2']
            },
            'field3': {
                'old': None,
                'new': item['field3']
            }
        }
        item_changes = get_item_changes(item, existing_item)
        self.assertEqual(item_changes, expected_item_changes)
