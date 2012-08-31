"Trie implementation in pure Python"
import array

try:
    from itertools import imap, repeat, tee
    iord = lambda s: imap(ord, s)
    char = chr
except ImportError:
    from itertools import repeat, tee
    iord = iter
    char = lambda o: bytes(chr(o), encoding='latin1')

try:
    from collections import abc
except ImportError:
    import collections as abc

STRING_TYPE = bytes
UNICODE_TYPE = str if str is not bytes else unicode


class Node(abc.MutableMapping):
    "Node object for Trie"

    def __init__(self):
        self._branches = array.array('B', repeat(0xFF, 256))
        self._children = 0
        self._nodes = []

    def __contains__(self, key):
        offset = self._branches[key]
        if offset >= len(self._nodes):
            return False
        return self._branches[key] is not None

    def __delitem__(self, key):
        offset = self._branches[key]
        if offset < len(self._nodes):
            self._nodes[offset] = None
            self._children -= 1

    def __getitem__(self, key):
        offset = self._branches[key]
        return self._nodes[offset] if offset < len(self._nodes) else None

    def __iter__(self):
        for key, offset in enumerate(self._branches):
            if offset >= len(self._nodes):
                continue
            yield (key, self._nodes[offset])

    def __len__(self):
        return self._children

    def __setitem__(self, key, node):
        current = self._branches[key]
        if current < len(self._nodes):
            self._nodes[current] = node
        else:
            leaf = len(self._nodes)
            self._nodes.append(node)
            self._branches[key] = leaf
            self._children += 1


class TrieBase(object):

    def __init__(self):
        self._root = Node()
        self._values = 0

    def __iter__(self):
        return self._iter(self._root, tuple())

    def __len__(self):
        return self._values

    def _make_path(self, key):
        encoded = False
        if isinstance(key, UNICODE_TYPE):
            encoded = True
            key = key.encode('UTF-8')
        if isinstance(key, STRING_TYPE):
            path = iord(key)
            return path, encoded
        else:
            raise TypeError("key must be string or bytes")

    def _delete(self, keys, node):
        try:
            index = next(keys)
            child = node[index]
            if child is None:
                raise AttributeError(index)
            leaf = self._delete(keys, child)
            if len(child) == 0:
                del node[index]
            return leaf
        except StopIteration:
            return node

    def _insert(self, keys, node):
        try:
            index = next(keys)
            child = node[index]
            if child is None:
                child = Node()
                node[index] = child
            return self._insert(keys, child)
        except StopIteration:
            return node

    def _iter(self, node, path):
        for node, path in self._walk(node, path):
            if not hasattr(node, 'value'):
                continue
            key = b''.join(char(v) for v in path)
            if node.encoded:
                key = key.decode('UTF-8')
            yield key

    def _search(self, keys, node):
        try:
            index = next(keys)
            child = node[index]
            if child is None:
                raise AttributeError(index)
            return self._search(keys, child)
        except StopIteration:
            return node

    def _walk(self, root, path):
        yield root, path
        for k1, n1 in root:
            p1 = path + (k1,)
            for n2, p2 in self._walk(n1, p1):
                yield n2, p2

    def startswith(self, base):
        try:
            path, encoded = self._make_path(base)
            p1, p2 = tee(path)
            root = self._search(p1, self._root)
            return self._iter(root, tuple(p2))
        except AttributeError:
            return iter([])
