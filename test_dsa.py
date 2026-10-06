"""Run with:  python -m pytest -q   (or just: python test_dsa.py)"""
import random
import tempfile

from dsa import AVLTree, CategoryTree, DocumentBST, Trie
from manager import DocumentManager


def build(keys, cls=DocumentBST):
    t = cls()
    for k in keys:
        assert t.insert(k, k.lower())
    return t


def check_avl(t):
    def rec(n, lo, hi):
        if n is None:
            return 0
        assert (lo is None or n.key > lo) and (hi is None or n.key < hi)
        l, r = rec(n.left, lo, n.key), rec(n.right, n.key, hi)
        assert abs(l - r) <= 1 and n.height == 1 + max(l, r)
        return n.height
    rec(t.root, None, None)


# ------------------------------------------------------------------ plain BST
def test_insert_search_duplicate():
    t = build(["M", "F", "T", "B", "H"])
    assert not t.insert("M", "x") and len(t) == 5
    assert t.find("H") == "h" and t.find("Z") is None
    assert t.search("H")[1] == ["M", "F", "H"]


def test_inorder_sorted():
    keys = [f"K{n:03d}" for n in random.sample(range(200), 100)]
    assert build(keys).inorder() == [k.lower() for k in sorted(keys)]


def test_delete_all_cases():
    t = build(["M", "F", "T", "B", "H", "P", "W", "G"])
    assert t.delete("B") and t.delete("H") and t.delete("M") and not t.delete("ZZZ")
    assert t.inorder() == ["f", "g", "p", "t", "w"] and len(t) == 5


def test_skewed_plain_bst_no_recursion_error():
    t = build([f"K{n:05d}" for n in range(5000)])
    assert t.height() == 5000 and len(t.inorder()) == 5000


def test_range_and_preorder_rebuild():
    t = build(["SAF-1", "MNT-1", "SAF-2", "QLT-1", "SAF-3"])
    assert t.range_query("SAF-", "SAF-\uffff") == ["saf-1", "saf-2", "saf-3"]
    r = DocumentBST()
    for k, v in t.preorder_items():
        r.insert(k, v)
    assert r.preorder_items() == t.preorder_items()


# ------------------------------------------------------------------------ AVL
def test_avl_sorted_inserts_stay_balanced():
    t = build([f"K{n:05d}" for n in range(5000)], AVLTree)
    check_avl(t)
    assert t.height() <= 18 and t.rotations > 0 and len(t) == 5000
    assert t.search("K04321")[0] == "k04321" and len(t.search("K04321")[1]) <= 18


def test_avl_random_insert_delete():
    keys = [f"K{n:03d}" for n in range(400)]
    random.shuffle(keys)
    t = build(keys, AVLTree)
    for k in random.sample(keys, 250):
        keys.remove(k)
        assert t.delete(k)
        check_avl(t)
    assert not t.delete("nope") and not t.insert(keys[0], "dup")
    assert t.inorder() == [k.lower() for k in sorted(keys)] and len(t) == 150


def test_avl_preorder_rebuild_same_contents():
    t = build([f"K{n:03d}" for n in range(100)], AVLTree)
    r = AVLTree()
    for k, v in t.preorder_items():
        r.insert(k, v)
    check_avl(r)
    assert r.inorder() == t.inorder()


# ----------------------------------------------------------------------- Trie
def make_trie():
    t = Trie()
    for w, d in [("safety", "1"), ("safety", "2"), ("safe", "3"), ("maintenance", "4"),
                 ("manual", "5"), ("inspection", "6")]:
        t.insert(w, d)
    return t


def test_trie_prefix_complete_remove():
    t = make_trie()
    assert t.docs_with_prefix("saf") == {"1", "2", "3"} and t.docs_with_prefix("x") == set()
    assert t.complete("ma") == ["maintenance", "manual"]
    t.remove("safe", "3")
    assert t.docs_with_prefix("saf") == {"1", "2"}
    t.remove("manual", "5")
    assert not t.has_prefix("manu") and t.has_prefix("main")


def test_trie_fuzzy():
    t = make_trie()
    assert t.fuzzy_words("maintenence", 2)[0] == ("maintenance", 1)
    assert "1" in t.fuzzy_docs("saftey", 1)           # transposition
    assert t.fuzzy_docs("inspecton", 1) == {"6": 0} or "6" in t.fuzzy_docs("inspecton", 1)
    assert t.fuzzy_docs("zzzzzz", 1) == {}


# -------------------------------------------------------------------- manager
def test_manager_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        m = DocumentManager(d)
        m.load_samples()
        assert len(m.bst) == 12
        ids = [x.doc_id for x in m.all_documents()]
        assert ids == sorted(ids)
        fire = m.by_category("Safety/Fire Safety")
        assert [x.version for x in fire] == [1, 2] and fire[0].status == "Superseded"
        assert len(m.search_id("SAF-")[0]) == 4
        assert len(m.search_text("saf")) == 4
        assert len(m.search_text("fire evac")) == 2
        assert m.search_text("maintenence") == [] and len(m.search_text("maintenence", fuzzy=True)) == 3
        assert m.corrections("safty") == [("safty", "safety")]
        assert m.autocomplete("fire ev") == ["fire evacuation"]
        assert m.delete_document("SAF-0004") and len(m.search_text("evacuation")) == 1
        m2 = DocumentManager(d)                       # reload from disk
        assert len(m2.bst) == 11 and len(m2.search_text("evacuation")) == 1
        assert [x.doc_id for x in m2.all_documents()] == [x.doc_id for x in m.all_documents()]
        check_avl(m2.bst)


def test_category_tree():
    c = CategoryTree.default()
    assert c.find("Safety/Fire Safety").path() == "Safety/Fire Safety"
    c.find("Safety").doc_ids.add("A")
    c.find("Safety/PPE & Hazards").doc_ids.add("B")
    assert c.subtree_doc_ids(c.find("Safety")) == {"A", "B"}
    assert CategoryTree.from_dict(c.to_dict()).find("Safety/PPE & Hazards").doc_ids == {"B"}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
