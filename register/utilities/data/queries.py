import json
import os
from datetime import datetime
from register import config
from register.app import app
from register.dependencies.rabbitmq import publish_message
from register.utilities.data.connection import start, commit, rollback
from register.utilities.data.empty_entry import create_empty_entry
from register.utilities.data.merkle_data import store_leaf_hash, prune_merkle_tree
from register.utilities.item_helper import get_action_type, get_item_changes
from register.utilities.leaf_hash import calculate_leaf_hash


def _insert_to_item_table(cursor, item, item_hash):
    # TODO(once we get PG 9.5, replace this with INSERT... ON CONFLICT DO
    # NOTHING)
    app.audit_logger.info("Consider inserting item with hash '%s'", item_hash)
    cursor.execute(
        'SELECT COUNT(*) AS c FROM item WHERE item_hash=%(hash)s', {'hash': item_hash})
    row = cursor.fetchone()
    if row['c'] > 0:
        app.audit_logger.info("Item with hash '%s' already exists", item_hash)
        return

    app.audit_logger.info("Insert item with hash '%s'", item_hash)
    cursor.execute("INSERT INTO item "
                   "(item_hash, item) "
                   "VALUES (%(hash)s, %(item)s)", {
                       "hash": item_hash,
                       "item": json.dumps(item)
                   })


def _insert_to_entry_table(cursor, timestamp, item_hash, item_key, item_signature):
    app.audit_logger.info(
        "Insert entry with timestamp '%s' and item hash '%s'", timestamp, item_hash)
    cursor.execute("INSERT INTO entry "
                   "(entry_timestamp, item_hash, key, item_signature) "
                   "VALUES (%(timestamp)s, %(hash)s, %(key)s, %(signature)s) "
                   "RETURNING entry_number", {
                       "timestamp": timestamp,
                       "hash": item_hash,
                       "key": item_key,
                       "signature": item_signature
                   })

    row = cursor.fetchone()
    return row['entry_number']


def insert_item_in_transaction(cursor, item, item_hash, item_signature):
    app.logger.info("Insert item '%s' in transaction", item_hash)
    key_field = app.config['REGISTER_KEY_FIELD']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    _insert_to_item_table(cursor, item, item_hash)
    entry_number = _insert_to_entry_table(
        cursor, timestamp, item_hash, item[key_field], item_signature)

    entry = {
        "entry-number": entry_number,
        "entry-timestamp": timestamp,
        "item-hash": item_hash,
        "key": item[key_field],
        "item-signature": item_signature
    }

    hash_bin = calculate_leaf_hash(entry)
    store_leaf_hash(cursor, entry_number, hash_bin.decode())

    existing_item = None
    key_name = os.environ['REGISTER_KEY_FIELD']
    existing_record = read_record_by_field_value(str(item[key_name]))

    if existing_record is not None:
        existing_item = existing_record['item']

    action_type = get_action_type(existing_item)

    message = entry
    message['action-type'] = action_type
    message['item'] = item

    if action_type == 'UPDATED':
        app.logger.info("Item '%s' is updated", item_hash)
        message['item-changes'] = get_item_changes(item, existing_item)

    prune_merkle_tree(cursor, entry_number)

    app.logger.info("Sending message to exchange %s", config.EXCHANGE_NAME)
    publish_message(message, config.RABBIT_URL, config.EXCHANGE_NAME, config.REGISTER_ROUTEKEY, queue_name=None,
                    exchange_type=config.EXCHANGE_TYPE, serializer="json",
                    headers=None)
    return entry_number


def insert_item(item, item_hash, item_signature):
    app.logger.info("Insert item")
    cursor = start()
    try:
        entry_number = insert_item_in_transaction(
            cursor, item, item_hash, item_signature)
        commit(cursor)
    except Exception:  # pragma: no cover
        rollback(cursor)
        raise
    return entry_number


def insert_items(item_list):
    app.logger.info("Insert items")
    result = []
    cursor = start()
    try:
        for item in item_list:
            entry_number = insert_item_in_transaction(
                cursor, item['item'], item['item-hash'], item['item-signature'])
            result.append({
                'item-hash': item['item-hash'],
                'entry-number': entry_number
            })
        commit(cursor)
    except Exception as e:  # pragma: no cover
        app.logger.exception(str(e))
        rollback(cursor)
        raise
    return result


def read_item(item_hash):
    app.logger.info("Read item '%s'", item_hash)
    cursor = start()
    try:
        cursor.execute('SELECT item FROM item '
                       'WHERE item_hash = %(hash)s', {'hash': item_hash})
        row = cursor.fetchone()
        if row is None:
            return None

        return row['item']
    finally:
        commit(cursor)


def read_entry(entry_number):
    app.logger.info("Read entry '%s'", str(entry_number))
    cursor = start()
    try:
        entry_count = count_entries(cursor)
        if int(entry_number) > entry_count:
            return None

        cursor.execute('SELECT entry_timestamp, item_hash, key, item_signature '
                       'FROM entry '
                       'WHERE entry_number=%(number)s', {
                           "number": entry_number
                       })
        row = cursor.fetchone()
        if row is None:
            return create_empty_entry(entry_number)

        return {
            "entry-number": entry_number,
            "entry-timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
            "item-hash": row['item_hash'],
            "key": row['key'],
            "item-signature": row['item_signature']
        }
    finally:
        commit(cursor)


def read_record_by_field_value(field_value):
    app.logger.info("Read record by field value '%s'", field_value)
    cursor = start()
    try:
        cursor.execute('SELECT e.entry_number, e.entry_timestamp, e.item_hash, e.key, i.item '
                       'FROM entry e, item i '
                       'WHERE e.item_hash = i.item_hash '
                       'AND key=%(key)s ORDER BY e.entry_number DESC LIMIT 1', {
                           'key': field_value
                       })
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "entry-number": row['entry_number'],
            "entry-timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
            "item-hash": row['item_hash'],
            "key": row['key'],
            "item": row['item']
        }

    finally:
        commit(cursor)


def count_entries(cursor):
    app.logger.info("Count entries")
    cursor.execute('SELECT COALESCE(MAX(entry_number), 0) AS count FROM entry')
    return cursor.fetchone()['count']


def read_entries(cursor, offset, limit, max_entry_number):
    app.logger.info("Read %s entries starting at %s", str(limit), str(offset))

    top_of_range = max_entry_number - offset
    bottom_of_range = top_of_range - limit
    if bottom_of_range < 0:
        bottom_of_range = 0

    cursor.execute('SELECT entry_number, entry_timestamp, item_hash, key, item_signature '
                   'FROM entry '
                   'WHERE entry_number > %(bottom)s AND entry_number <= %(top)s '
                   'ORDER BY entry_number DESC',
                   {'bottom': bottom_of_range, 'top': top_of_range})
    rows = cursor.fetchall()
    result = []

    entry_dict = {}
    for row in rows:
        entry = {
            "entry-number": row['entry_number'],
            "entry-timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
            "item-hash": row['item_hash'],
            "key": row['key'],
            "entry-signature": row['item_signature']
        }
        entry_dict[int(row['entry_number'])] = entry

    for i in range(top_of_range, bottom_of_range, -1):
        if i in entry_dict:
            result.append(entry_dict[i])
        else:
            result.append(create_empty_entry(i))

    return result


def read_item_entries(item_hash):
    app.logger.info("Read item entries for '%s'", item_hash)
    cursor = start()
    try:
        cursor.execute('SELECT entry_number, entry_timestamp, item_hash, key, item_signature '
                       'FROM entry '
                       'WHERE item_hash = %(hash)s'
                       'ORDER BY entry_number DESC', {
                           'hash': item_hash
                       })
        rows = cursor.fetchall()
        if len(rows) == 0:
            app.logger.warning("No item entries found for '%s'", item_hash)
            return None

        result = []

        for row in rows:
            result.append({
                "entry-number": row['entry_number'],
                "entry-timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                "item-hash": row['item_hash'],
                "key": row['key'],
                "item-signature": row['item_signature']
            })

        app.logger.info("%d item entries returned", len(result))
        return result
    finally:
        commit(cursor)


def read_record_entries(field_value):
    app.logger.info("Read record entries for '%s'", field_value)
    cursor = start()
    try:
        cursor.execute('SELECT entry_number, entry_timestamp, item_hash, key '
                       'FROM entry '
                       'WHERE key=%(key)s ORDER BY entry_number DESC', {
                           'key': field_value
                       })
        rows = cursor.fetchall()
        if len(rows) == 0:
            app.logger.warning("No record entries found for '%s'", field_value)
            return None

        result = []
        for row in rows:
            result.append({
                "entry-number": row['entry_number'],
                "entry-timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                "item-hash": row['item_hash'],
                "key": row['key']
            })
        app.logger.info("%d record entries returned", len(result))
        return result

    finally:
        commit(cursor)


def republish_entry(entry_number, routing_key):
    app.logger.info("Republishing entry '%s'", entry_number)
    cursor = start()
    try:
        max_entry = count_entries(cursor)

        if entry_number > max_entry:
            app.logger.warning(
                "Entry number '%s' is greater than maximum entry '%s'", entry_number, max_entry)
            return False

        cursor.execute('SELECT e.entry_number, e.entry_timestamp, e.item_hash, e.key, i.item, e.item_signature '
                       'FROM entry e '
                       'JOIN item i on e.item_hash = i.item_hash '
                       'WHERE entry_number=%(entry_number)s LIMIT 1', {
                           'entry_number': entry_number
                       })
        entry_row = cursor.fetchone()
        prev_item = None
        if not entry_row:
            app.logger.info(
                "No entry found for '%s', using empty entry", entry_number)
            entry = create_empty_entry(entry_number)
        else:
            entry = {
                "entry-number": entry_number,
                "entry-timestamp": entry_row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                "item-hash": entry_row['item_hash'],
                "key": entry_row['key'],
                "item-signature": entry_row['item_signature'],
                "item": entry_row['item']
            }

            cursor.execute('SELECT e.entry_number, i.item '
                           'FROM entry e '
                           'JOIN item i on e.item_hash = i.item_hash '
                           'WHERE e.key=%(key)s AND entry_number < %(entry_number)s '
                           'ORDER BY entry_number DESC LIMIT 1', {
                               'key': entry['key'],
                               'entry_number': entry_number
                           })
            prev_entry_row = cursor.fetchone()
            if prev_entry_row:
                prev_item = prev_entry_row['item']

        action_type = get_action_type(prev_item)

        message = entry
        message['action-type'] = action_type

        if action_type == 'UPDATED':
            message['item-changes'] = get_item_changes(
                entry['item'], prev_item)
            app.logger.info("Created republish for entry '%s' with changes from previous entry '%s'", entry_number,
                            prev_entry_row['entry_number'])
        else:
            app.logger.info("Created republish for entry '%s''", entry_number)

        app.logger.info("Sending republish message to exchange '%s' with routing key '%s'",
                        config.EXCHANGE_NAME, routing_key)
        app.logger.debug("Sending message '%s''", message)
        publish_message(message, config.RABBIT_URL, config.EXCHANGE_NAME, routing_key, queue_name=None,
                        exchange_type=config.EXCHANGE_TYPE, serializer="json",
                        headers=None)

        app.audit_logger.info(
            "Entry '%s' republished to routing key '%s'", entry_number, routing_key)
        return True

    finally:
        commit(cursor)


def count_all_records(cursor):
    app.logger.info("Count all records")
    cursor.execute('select count(distinct(key)) from entry')
    return cursor.fetchone()['count']


def read_all_records(offset, limit):
    app.logger.info("Read %s records from %s", str(limit), str(offset))
    key_field = app.config['REGISTER_KEY_FIELD']

    cursor = start()
    number = count_all_records(cursor)
    try:
        cursor.execute('SELECT e2.entry_number, e2.entry_timestamp, e2.item_hash, e2.key, i.item '
                       'FROM entry e2, item i '
                       'WHERE e2.item_hash = i.item_hash '
                       'AND e2.entry_number IN ( '
                       '  SELECT MAX(e.entry_number) '
                       '  FROM entry e '
                       '  GROUP BY e.key '
                       ') '
                       'ORDER BY e2.entry_number ASC '
                       'LIMIT %(limit)s OFFSET %(offset)s',
                       {'limit': limit, 'offset': offset})
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            result[row['key']] = {
                "entry-number": row['entry_number'],
                "entry_timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                "item-hash": row['item_hash'],
                key_field: row['key'],
                'item': row['item']
            }
        app.logger.info("%d records returned", len(result))
        return result, number
    finally:
        commit(cursor)


def read_records_by_attribute(field_name, field_value):
    # TODO(pagination)
    app.logger.info("Read records where %s = %s", field_name, field_value)
    app.logger.warning("read_records_by_attribute: pagination not implemented")
    key_field = app.config['REGISTER_KEY_FIELD']

    cursor = start()
    try:
        cursor.execute("SELECT e.entry_number, e.entry_timestamp, e.item_hash, e.key, "
                       "       i.item "
                       "FROM entry e, item i "
                       "WHERE e.item_hash = i.item_hash "
                       "AND i.item @> %(field)s "
                       "ORDER BY e.entry_number ASC", {
                           'field': json.dumps({field_name: field_value})
                       })

        rows = cursor.fetchall()
        result = {}
        for row in rows:
            result[row['key']] = {
                "entry-number": row['entry_number'],
                "entry_timestamp": row['entry_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                "item-hash": row['item_hash'],
                key_field: row['key'],
                'item': row['item']
            }
        app.logger.info("%d records returned", len(result))
        return result
    finally:
        commit(cursor)


def count_items(cursor):
    app.logger.info("Count items")
    cursor.execute('SELECT COUNT(*) AS count FROM item')
    return cursor.fetchone()['count']


def get_lastest_update(cursor):
    app.logger.info("Get latest update")
    cursor.execute('SELECT MAX(entry_timestamp) AS time FROM entry')
    row_time = cursor.fetchone()['time']
    return row_time.strftime('%Y-%m-%d %H:%M:%S.%f') if row_time is not None else None
