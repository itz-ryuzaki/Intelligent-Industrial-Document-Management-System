"""Core data structures for the Intelligent Industrial Document Management System.

* DocumentBST   - Binary Search Tree keyed on document ID (insert / search / delete /
                  inorder / range query). All operations are iterative so a skewed tree
                  can never hit Python's recursion limit.
* AVLTree       - self-balancing BST (subclass of DocumentBST) used as the live index
* Trie          - word index: prefix search, autocomplete, fuzzy (edit-distance) search
* CategoryTree  - general (n-ary) tree for Safety / Maintenance / Quality / HR ...
"""
from __future__ import annotations

import re
from typing import Any, Iterator, Optional


# --------------------------------------------------------------------------- BST
class BSTNode:
    __slots__ = ("key", "value", "left", "right")

    def __init__(self, key: str, value: Any):
        self.key, self.value = key, value
        self.left: Optional[BSTNode] = None
        self.right: Optional[BSTNode] = None


class DocumentBST:
    def __init__(self) -> None:
        self.root: Optional[BSTNode] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: str) -> bool:
        return self.search(key)[0] is not None

    # -- insert: O(h) ------------------------------------------------------
    def insert(self, key: str, value: Any) -> bool:
        """Insert; returns False (and changes nothing) if the key already exists."""
        new = BSTNode(key, value)
        if self.root is None:
            self.root = new
        else:
            cur = self.root
            while True:
                if key == cur.key:
                    return False
                side = "left" if key < cur.key else "right"
                nxt = getattr(cur, side)
                if nxt is None:
                    setattr(cur, side, new)
                    break
                cur = nxt
        self._size += 1
        return True

    # -- search: O(h) ------------------------------------------------------
    def search(self, key: str) -> tuple[Any, list[str]]:
        """Return (value or None, list of keys visited on the way down)."""
        path: list[str] = []
        cur = self.root
        while cur is not None:
            path.append(cur.key)
            if key == cur.key:
                return cur.value, path
            cur = cur.left if key < cur.key else cur.right
        return None, path

    def find(self, key: str) -> Any:
        return self.search(key)[0]

    # -- delete: O(h), handles leaf / one child / two children -------------
    def delete(self, key: str) -> bool:
        parent, cur = None, self.root
        while cur is not None and cur.key != key:
            parent, cur = cur, (cur.left if key < cur.key else cur.right)
        if cur is None:
            return False
        if cur.left is not None and cur.right is not None:
            # two children: copy inorder successor here, then remove the successor
            sp, s = cur, cur.right
            while s.left is not None:
                sp, s = s, s.left
            cur.key, cur.value = s.key, s.value
            parent, cur = sp, s
        child = cur.left if cur.left is not None else cur.right
        if parent is None:
            self.root = child
        elif parent.left is cur:
            parent.left = child
        else:
            parent.right = child
        self._size -= 1
        return True

    # -- traversals --------------------------------------------------------
    def _inorder_nodes(self) -> Iterator[tuple[BSTNode, int, Optional[str]]]:
        """Iterative inorder yielding (node, depth, parent_key)."""
        stack: list[tuple[BSTNode, int, Optional[str]]] = []
        cur, depth, pkey = self.root, 0, None
        while stack or cur is not None:
            while cur is not None:
                stack.append((cur, depth, pkey))
                pkey, cur, depth = cur.key, cur.left, depth + 1
            node, depth, pkey = stack.pop()
            yield node, depth, pkey
            pkey, cur, depth = node.key, node.right, depth + 1

    def inorder(self) -> list[Any]:
        """Values in ascending key order -> sorted document listing."""
        return [n.value for n, _, _ in self._inorder_nodes()]

    def preorder_items(self) -> list[tuple[str, Any]]:
        """Preorder (root first): re-inserting in this order rebuilds the same shape."""
        out, stack = [], [self.root] if self.root else []
        while stack:
            n = stack.pop()
            out.append((n.key, n.value))
            if n.right:
                stack.append(n.right)
            if n.left:
                stack.append(n.left)
        return out

    def range_query(self, lo: str, hi: str) -> list[Any]:
        """All values with lo <= key <= hi; prunes subtrees outside the range."""
        out, stack, cur = [], [], self.root
        while stack or cur is not None:
            while cur is not None:
                stack.append(cur)
                cur = cur.left if cur.key >= lo else None
            n = stack.pop()
            if n.key > hi:
                break
            if n.key >= lo:
                out.append(n.value)
            cur = n.right
        return out

    def height(self) -> int:
        if self.root is None:
            return 0
        return max(d for _, d, _ in self._inorder_nodes()) + 1

    def layout(self) -> list[tuple[str, int, int, Optional[str]]]:
        """(key, depth, x_index, parent_key) for drawing."""
        return [(n.key, d, i, p) for i, (n, d, p) in enumerate(self._inorder_nodes())]


# --------------------------------------------------------------- Category tree
class CategoryNode:
    def __init__(self, name: str, parent: Optional["CategoryNode"] = None):
        self.name = name
        self.parent = parent
        self.children: list[CategoryNode] = []
        self.doc_ids: set[str] = set()

    def path(self) -> str:
        parts, n = [], self
        while n.parent is not None:
            parts.append(n.name)
            n = n.parent
        return "/".join(reversed(parts))


class CategoryTree:
    ROOT_NAME = "All Documents"

    def __init__(self) -> None:
        self.root = CategoryNode(self.ROOT_NAME)

    def find(self, path: str) -> Optional[CategoryNode]:
        node = self.root
        for part in filter(None, path.split("/")):
            node = next((c for c in node.children if c.name == part), None)
            if node is None:
                return None
        return node

    def add(self, parent_path: str, name: str) -> CategoryNode:
        name = name.strip()
        parent = self.find(parent_path)
        if parent is None:
            raise ValueError("Parent category not found")
        if not name or "/" in name:
            raise ValueError("Category name must be non-empty and cannot contain '/'")
        if any(c.name.lower() == name.lower() for c in parent.children):
            raise ValueError(f"'{name}' already exists here")
        node = CategoryNode(name, parent)
        parent.children.append(node)
        return node

    def remove(self, path: str) -> None:
        node = self.find(path)
        if node is None or node is self.root:
            raise ValueError("Cannot remove this category")
        if node.children or node.doc_ids:
            raise ValueError("Category is not empty")
        node.parent.children.remove(node)

    def walk(self) -> Iterator[CategoryNode]:
        """DFS over every node except the root."""
        stack = list(reversed(self.root.children))
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))

    def subtree_doc_ids(self, node: CategoryNode) -> set[str]:
        ids, stack = set(), [node]
        while stack:
            n = stack.pop()
            ids |= n.doc_ids
            stack.extend(n.children)
        return ids

    def locate_doc(self, doc_id: str) -> Optional[CategoryNode]:
        return next((n for n in self.walk() if doc_id in n.doc_ids), None)

    # -- persistence -------------------------------------------------------
    def to_dict(self, node: Optional[CategoryNode] = None) -> dict:
        node = node or self.root
        return {"name": node.name, "docs": sorted(node.doc_ids),
                "children": [self.to_dict(c) for c in node.children]}

    @classmethod
    def from_dict(cls, data: dict) -> "CategoryTree":
        tree = cls()

        def build(d: dict, node: CategoryNode) -> None:
            node.doc_ids = set(d.get("docs", []))
            for cd in d.get("children", []):
                child = CategoryNode(cd["name"], node)
                node.children.append(child)
                build(cd, child)

        build(data, tree.root)
        return tree

    @classmethod
    def default(cls) -> "CategoryTree":
        tree = cls()
        layout = {
            "Safety": ["Fire Safety", "PPE & Hazards", "Incident Reports"],
            "Maintenance": ["Preventive", "Breakdown", "Equipment Manuals"],
            "Quality": ["Inspection", "Audits", "ISO Standards"],
            "HR": ["Training", "Policies"],
        }
        for top, subs in layout.items():
            tree.add("", top)
            for s in subs:
                tree.add(top, s)
        return tree


# -------------------------------------------------------------------- AVL tree
class AVLNode(BSTNode):
    __slots__ = ("height",)

    def __init__(self, key: str, value: Any):
        super().__init__(key, value)
        self.height = 1


def _h(n: Optional[AVLNode]) -> int:
    return n.height if n else 0


def _update(n: AVLNode) -> None:
    n.height = 1 + max(_h(n.left), _h(n.right))


def _balance(n: AVLNode) -> int:
    return _h(n.left) - _h(n.right)


class AVLTree(DocumentBST):
    """Self-balancing BST: |height(left) - height(right)| <= 1 at every node, so
    search / insert / delete stay O(log n) whatever the insertion order.
    Reuses search, traversals, range_query and layout from DocumentBST.
    Recursion depth is O(log n), so recursive insert/delete are safe here."""

    def __init__(self) -> None:
        super().__init__()
        self.rotations = 0

    def _rot_right(self, y: AVLNode) -> AVLNode:
        x = y.left
        y.left, x.right = x.right, y
        _update(y), _update(x)
        self.rotations += 1
        return x

    def _rot_left(self, x: AVLNode) -> AVLNode:
        y = x.right
        x.right, y.left = y.left, x
        _update(x), _update(y)
        self.rotations += 1
        return y

    def _rebalance(self, n: AVLNode) -> AVLNode:
        _update(n)
        b = _balance(n)
        if b > 1:                                   # left heavy
            if _balance(n.left) < 0:                # left-right case
                n.left = self._rot_left(n.left)
            return self._rot_right(n)
        if b < -1:                                  # right heavy
            if _balance(n.right) > 0:               # right-left case
                n.right = self._rot_right(n.right)
            return self._rot_left(n)
        return n

    def insert(self, key: str, value: Any) -> bool:
        added = [True]

        def ins(n):
            if n is None:
                return AVLNode(key, value)
            if key == n.key:
                added[0] = False
                return n
            if key < n.key:
                n.left = ins(n.left)
            else:
                n.right = ins(n.right)
            return self._rebalance(n)

        self.root = ins(self.root)
        if added[0]:
            self._size += 1
        return added[0]

    def delete(self, key: str) -> bool:
        removed = [False]

        def rem(n, k):
            if n is None:
                return None
            if k < n.key:
                n.left = rem(n.left, k)
            elif k > n.key:
                n.right = rem(n.right, k)
            else:
                removed[0] = True
                if n.left is None:
                    return n.right
                if n.right is None:
                    return n.left
                s = n.right                          # inorder successor
                while s.left is not None:
                    s = s.left
                n.key, n.value = s.key, s.value
                n.right = rem(n.right, s.key)
            return self._rebalance(n)

        self.root = rem(self.root, key)
        if removed[0]:
            self._size -= 1
        return removed[0]

    def height(self) -> int:          # O(1): stored on the root
        return _h(self.root)


# ------------------------------------------------------------------------ Trie
def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def max_edits(n: int) -> int:
    """Typo budget by word length: short words must match exactly."""
    return 0 if n <= 3 else 1 if n <= 7 else 2


class TrieNode:
    __slots__ = ("children", "doc_ids")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.doc_ids: set[str] = set()   # non-empty => a word ends here


class Trie:
    """Word index: prefix search, autocomplete and typo-tolerant (fuzzy) search."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str, doc_id: str) -> None:
        n = self.root
        for ch in word:
            n = n.children.setdefault(ch, TrieNode())
        n.doc_ids.add(doc_id)

    def remove(self, word: str, doc_id: str) -> None:
        path = [self.root]
        for ch in word:
            nxt = path[-1].children.get(ch)
            if nxt is None:
                return
            path.append(nxt)
        path[-1].doc_ids.discard(doc_id)
        for i in range(len(word), 0, -1):            # prune dead branches
            if path[i].doc_ids or path[i].children:
                break
            del path[i - 1].children[word[i - 1]]

    def _node(self, prefix: str) -> Optional[TrieNode]:
        n = self.root
        for ch in prefix:
            n = n.children.get(ch)
            if n is None:
                return None
        return n

    def has_prefix(self, prefix: str) -> bool:
        return self._node(prefix) is not None

    def docs_with_prefix(self, prefix: str) -> set[str]:
        """O(len(prefix) + size of matching subtree) - independent of total docs."""
        start, out = self._node(prefix), set()
        stack = [start] if start else []
        while stack:
            n = stack.pop()
            out |= n.doc_ids
            stack.extend(n.children.values())
        return out

    def complete(self, prefix: str, limit: int = 8) -> list[str]:
        """Autocomplete: up to `limit` words starting with prefix, alphabetical."""
        start, out = self._node(prefix), []
        stack = [(start, prefix)] if start else []
        while stack and len(out) < limit:
            n, w = stack.pop()
            if n.doc_ids:
                out.append(w)
            for ch in sorted(n.children, reverse=True):
                stack.append((n.children[ch], w + ch))
        return out

    # -- fuzzy search: edit-distance DP carried down the trie -----------------
    def _fuzzy(self, q: str, k: int):
        """Walk the trie keeping one Damerau-Levenshtein (OSA) row per node.
        Yields (node, word, dist_of_word, best_dist_of_any_prefix). Branches are
        pruned once no prefix within k edits of q can exist below them."""
        n = len(q)
        stack = [(self.root, "", list(range(n + 1)), None, n)]
        while stack:
            node, word, row, prow, best = stack.pop()
            yield node, word, row[-1], best
            for ch, child in node.children.items():
                new = [row[0] + 1]
                for i in range(1, n + 1):
                    v = min(new[i - 1] + 1, row[i] + 1, row[i - 1] + (q[i - 1] != ch))
                    if prow is not None and i > 1 and q[i - 1] == word[-1] and q[i - 2] == ch:
                        v = min(v, prow[i - 2] + 1)      # transposition (e.g. safte -> safet)
                    new.append(v)
                nb = min(best, new[-1])
                if min(new) <= k or nb <= k:
                    stack.append((child, word + ch, new, row, nb))

    def fuzzy_docs(self, q: str, k: int) -> dict[str, int]:
        """doc_id -> edit distance, for docs having a word whose prefix is within k
        edits of q (so partly-typed, misspelled words still match)."""
        out: dict[str, int] = {}
        for node, _, _, best in self._fuzzy(q, k):
            if best <= k:
                for d in node.doc_ids:
                    out[d] = min(out.get(d, k + 1), best)
        return out

    def fuzzy_words(self, q: str, k: int) -> list[tuple[str, int]]:
        """Whole words within k edits of q, closest first ("did you mean")."""
        hits = [(w, d) for node, w, d, _ in self._fuzzy(q, k) if node.doc_ids and d <= k]
        return sorted(hits, key=lambda x: (x[1], x[0]))
