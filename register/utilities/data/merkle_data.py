from register.app import app
from register.utilities.data.empty_entry import create_empty_entry
from register.utilities.leaf_hash import calculate_leaf_hash


class MerkleData(object):
    # By carefully managing un-needed branch hashes, the number of pre-calculated branch
    # hashes will not exceed <number of entries> - 1.
    # With 32-byte hashes this means
    #   Stored as string (64 chars): 64bytes * 26M = 1.5Gb
    #   Consider storing in a binary format

    def __init__(self, cursor):
        self.cursor = cursor
        self._leaf_count = None
        self._leaf_hashes = {}

    def leaf_hash(self, entry_number):
        app.logger.info("Read entry hash for entry number %s", str(entry_number))
        self.cursor.execute('SELECT entry_hash FROM leaf_hashes '
                            'WHERE entry_number=%(number)s',
                            {'number': entry_number})
        row = self.cursor.fetchone()
        if row is None:
            app.logger.error("No row found for entry %s", str(entry_number))
            return calculate_leaf_hash(create_empty_entry(entry_number)).decode()
        return row['entry_hash']

    def branch_hash(self, start, length):
        # Merkle Tree is start, length; Table is start, end - for Reasons that might
        # turn out to be good (they haven't, though the range-killing mentioned below might require it).
        # Also, start is 0-based (sigh), table is entry-number (1-based)
        range_start = start + 1
        range_end = (range_start + length) - 1
        app.logger.info("Read branch hash for %s leaves from %s", str(length), str(start))
        self.cursor.execute('SELECT branch_hash FROM branch_hashes '
                            'WHERE start_entry_number=%(start)s AND '
                            '      end_entry_number=%(end)s', {
                                'start': range_start,
                                'end': range_end
                            })
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row['branch_hash']

    def save_branch_hash(self, start, length, hash_string):
        range_start = start + 1
        range_end = (range_start + length) - 1
        app.audit_logger.info("Insert branch hash for %s leaves from %s", str(length), str(start))
        self.cursor.execute('INSERT INTO branch_hashes '
                            '(start_entry_number, end_entry_number, branch_hash) VALUES '
                            '(%(start)s, %(end)s, %(hash)s)', {
                                'start': range_start,
                                'end': range_end,
                                'hash': hash_string
                            })

    def leaf_count(self):
        if self._leaf_count is None:
            app.logger.info("Get leaf count")
            self.cursor.execute('SELECT COUNT(*) AS count FROM leaf_hashes ')
            self._leaf_count = self.cursor.fetchone()['count']
        return self._leaf_count

    @staticmethod
    def is_power_of_2(value):
        return value != 0 and ((value & (value - 1)) == 0)


def store_leaf_hash(cursor, entry_number, leaf_hash):
    app.audit_logger.info("Insert leaf_hash for entry %s", str(entry_number))
    cursor.execute('INSERT INTO leaf_hashes '
                   '(entry_number, entry_hash) VALUES (%(number)s, %(hash)s)', {
                       'number': entry_number,
                       'hash': leaf_hash
                   })


def prune_merkle_tree(cursor, end_entry):
    # Here we benefit from the tables being entry-number rather than index...
    app.logger.info("Prune merkle tree")
    previous_entry = end_entry - 1
    if not MerkleData.is_power_of_2(previous_entry):
        app.audit_logger.info("Delete from branch hashes ranges up to %s", str(end_entry))
        cursor.execute('DELETE FROM branch_hashes WHERE end_entry_number=%(number)s', {
            'number': previous_entry
        })
