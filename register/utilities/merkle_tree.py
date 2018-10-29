from register.exceptions import ApplicationError
from Crypto.Hash import SHA256
from base64 import b16encode


class MerkleTree(object):
    def __init__(self, data_store):
        self.data_store = data_store

    def _k(self, n):
        if n <= 1:
            raise ApplicationError("Cannot calculate k for values of 1 or less", "E102")

        s = 1
        while s < n:
            s <<= 1

        return s >> 1

    def tree_size(self):
        return self.data_store.leaf_count()

    def root_hash(self):
        hash_bytes = self._branch_hash(0, self.tree_size())
        return hash_bytes

    def entry_proof(self, entry_number, total_entries):
        # TODO(We're going to assume that the leaf index is entry_number-1)
        return self._sub_entry_proof(entry_number - 1, 0, total_entries)

    def entry_leaf_hash(self, entry_number):
        return bytes.fromhex(self.data_store.leaf_hash(entry_number))

    def consistency_proof(self, tree_1_size, tree_2_size):
        if tree_1_size <= 0:
            raise ApplicationError("Cannot calculate consistency for a tree size of 0", "E103")

        if tree_2_size < tree_1_size:
            raise ApplicationError("Cannot calculate consistency where tree 2 is smaller than tree 1", "E104")

        return self._sub_consistency_proof(tree_1_size, tree_2_size, 0, True)

    def _sub_consistency_proof(self, low, high, start, start_from_old):
        if low == high:
            if start_from_old:
                return []
            else:
                return [self._branch_hash(start, high, save_hash=False)]
        else:
            k = self._k(high)
            if low <= k:
                consistency_set = self._sub_consistency_proof(low, k, start, start_from_old)
                consistency_set.append(self._branch_hash(start + k, high - k, save_hash=False))
            else:
                consistency_set = self._sub_consistency_proof(low - k, high - k, start + k, False)
                consistency_set.append(self._branch_hash(start, k, save_hash=False))
            return consistency_set

    def _branch_hash(self, start, size, save_hash=True):
        if size == 0:
            return self._empty_hash()
        elif size == 1:
            return bytes.fromhex(self.data_store.leaf_hash(start + 1))
        else:
            cached_hash = self.data_store.branch_hash(start, size)
            if cached_hash is not None:
                return bytes.fromhex(cached_hash)

            k = self._k(size)
            left = self._branch_hash(start, k)
            right = self._branch_hash(k + start, size - k)
            branch_hash = self._tree_hash(left, right)
            if save_hash:
                self.data_store.save_branch_hash(start, size, b16encode(branch_hash).decode())
            return branch_hash

    def _tree_hash(self, left, right):
        digest = SHA256.new()
        digest.update(b'\x01')
        digest.update(left)
        digest.update(right)
        return digest.digest()

    def _empty_hash(self):
        return SHA256.new('').digest()

    def _sub_entry_proof(self, leaf_index, start, size):
        if size <= 1:
            return []

        k = self._k(size)
        if leaf_index < k:
            path = self._sub_entry_proof(leaf_index, start, k)
            path.append(self._branch_hash(start + k, size - k))
        else:
            path = self._sub_entry_proof(leaf_index - k, start + k, size - k)
            path.append(self._branch_hash(start, k))
        return path
