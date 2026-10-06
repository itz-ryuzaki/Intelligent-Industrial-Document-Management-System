"""Document manager: glues the BST index, the category tree and disk storage together."""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dsa import AVLTree, CategoryTree, Trie, max_edits, tokenize

BASE_DIR = Path(__file__).resolve().parent / "data"
PREFIXES = {"Safety": "SAF", "Maintenance": "MNT", "Quality": "QLT", "HR": "HRD"}


@dataclass
class Document:
    doc_id: str
    title: str
    category: str          # e.g. "Safety/Fire Safety"
    version: int = 1
    status: str = "Active"  # Active | Superseded
    description: str = ""
    file_path: str = ""     # stored copy ("" if no file attached)
    uploaded_at: str = ""


class DocumentManager:
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base = Path(base_dir)
        self.files_dir = self.base / "files"
        self.db_path = self.base / "documents.json"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.bst = AVLTree()   # self-balancing index keyed on document ID
        self.trie = Trie()     # word index for prefix / autocomplete / fuzzy search
        self.tree = CategoryTree.default()
        self.counters: dict[str, int] = {}
        self.load()

    # ------------------------------------------------------------ persistence
    def load(self) -> None:
        if not self.db_path.exists():
            return
        data = json.loads(self.db_path.read_text())
        self.tree = CategoryTree.from_dict(data["categories"])
        self.counters = data.get("counters", {})
        for d in data["documents"]:  # saved in preorder
            doc = Document(**d)
            self.bst.insert(doc.doc_id, doc)
            self._index(doc)

    def save(self) -> None:
        data = {"categories": self.tree.to_dict(), "counters": self.counters,
                "documents": [asdict(v) for _, v in self.bst.preorder_items()]}
        self.db_path.write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------- CRUD
    def _next_id(self, category: str) -> str:
        top = category.split("/")[0]
        prefix = PREFIXES.get(top, (top[:3] or "DOC").upper())
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return f"{prefix}-{self.counters[prefix]:04d}"

    def add_document(self, title: str, category: str, description: str = "",
                     source_file: str = "") -> Document:
        node = self.tree.find(category)
        if node is None or node is self.tree.root:
            raise ValueError("Choose a valid category")
        if not title.strip():
            raise ValueError("Title is required")

        # versioning: a newer upload with the same title+category supersedes older ones
        version = 1
        for old in self.bst.inorder():
            if old.category == category and old.title.lower() == title.strip().lower():
                version = max(version, old.version + 1)
                old.status = "Superseded"

        doc_id = self._next_id(category)
        stored = ""
        if source_file:
            dest = self.files_dir / f"{doc_id}_{Path(source_file).name}"
            shutil.copy2(source_file, dest)
            stored = str(dest)
        doc = Document(doc_id, title.strip(), category, version, "Active", description.strip(),
                       stored, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.bst.insert(doc_id, doc)
        node.doc_ids.add(doc_id)
        self._index(doc)
        self.save()
        return doc

    def delete_document(self, doc_id: str) -> bool:
        doc = self.bst.find(doc_id)
        if doc is None:
            return False
        self.bst.delete(doc_id)
        self._unindex(doc)
        node = self.tree.locate_doc(doc_id)
        if node:
            node.doc_ids.discard(doc_id)
        if doc.file_path:
            Path(doc.file_path).unlink(missing_ok=True)
        self.save()
        return True

    # ---------------------------------------------------------------- queries
    def all_documents(self) -> list[Document]:
        return self.bst.inorder()  # inorder traversal = sorted by ID

    def by_category(self, path: str) -> list[Document]:
        node = self.tree.find(path)
        if node is None:
            return []
        docs = [self.bst.find(i) for i in self.tree.subtree_doc_ids(node)]  # O(log n) each
        return sorted((d for d in docs if d), key=lambda d: d.doc_id)

    def search_id(self, text: str) -> tuple[list[Document], list[str]]:
        """Exact ID lookup via BST; falls back to prefix range query (e.g. 'SAF-')."""
        key = text.strip().upper()
        doc, path = self.bst.search(key)
        if doc is not None:
            return [doc], path
        return self.bst.range_query(key, key + "\uffff"), path

    # ------------------------------------------------ text search (Trie)
    @staticmethod
    def _tokens(d: Document) -> set[str]:
        return set(tokenize(f"{d.doc_id} {d.title} {d.category} {d.description}"))

    def _index(self, d: Document) -> None:
        for t in self._tokens(d):
            self.trie.insert(t, d.doc_id)

    def _unindex(self, d: Document) -> None:
        for t in self._tokens(d):
            self.trie.remove(t, d.doc_id)

    def search_text(self, text: str, fuzzy: bool = False) -> list[Document]:
        """Every word in `text` must match (as a prefix, or within the typo budget
        when fuzzy). Results are ranked by total edit distance, then ID."""
        result: dict[str, int] | None = None
        for tok in tokenize(text):
            if fuzzy:
                hits = self.trie.fuzzy_docs(tok, max_edits(len(tok)))
            else:
                hits = dict.fromkeys(self.trie.docs_with_prefix(tok), 0)
            result = hits if result is None else {i: result[i] + s for i, s in hits.items() if i in result}
            if not result:
                return []
        scored = [(s, self.bst.find(i)) for i, s in (result or {}).items()]
        scored = [(s, d) for s, d in scored if d]
        return [d for s, d in sorted(scored, key=lambda x: (x[0], x[1].doc_id))]

    def autocomplete(self, text: str, limit: int = 8) -> list[str]:
        if not text or text[-1].isspace():
            return []
        head, _, last = text.rpartition(" ")
        words = [w for w in self.trie.complete(last.lower(), limit) if w != last.lower()]
        return [(head + " " if head else "") + w for w in words]

    def corrections(self, text: str) -> list[tuple[str, str]]:
        """'Did you mean' pairs for words that don't exist in the index."""
        out = []
        for tok in tokenize(text):
            if not self.trie.has_prefix(tok):
                words = self.trie.fuzzy_words(tok, max_edits(len(tok)))
                if words:
                    out.append((tok, words[0][0]))
        return out

    def category_paths(self) -> list[str]:
        return [n.path() for n in self.tree.walk()]

    def add_category(self, parent: str, name: str) -> None:
        self.tree.add(parent, name)
        self.save()

    def remove_category(self, path: str) -> None:
        self.tree.remove(path)
        self.save()

    def load_samples(self) -> int:
        samples = [
            ("Fire Evacuation Procedure", "Safety/Fire Safety", "Assembly points and exit routes"),
            ("Boiler Preventive Maintenance Schedule", "Maintenance/Preventive", "Quarterly checklist"),
            ("Incoming Material Inspection SOP", "Quality/Inspection", "Sampling plan and acceptance criteria"),
            ("New Joiner Induction Deck", "HR/Training", "Week 1 induction material"),
            ("PPE Usage Guidelines", "Safety/PPE & Hazards", "Helmets, gloves, eye protection"),
            ("CNC Lathe Operation Manual", "Maintenance/Equipment Manuals", "Model CL-450"),
            ("ISO 9001 Internal Audit Report", "Quality/Audits", "Annual internal audit findings"),
            ("Leave & Attendance Policy", "HR/Policies", "Applicable to all plant staff"),
            ("Chemical Spill Incident Report", "Safety/Incident Reports", "Line 3, minor spill"),
            ("Conveyor Breakdown Log", "Maintenance/Breakdown", "Motor failure analysis"),
            ("ISO 14001 Compliance Checklist", "Quality/ISO Standards", "Environmental standard"),
            ("Fire Evacuation Procedure", "Safety/Fire Safety", "Revised after drill (v2)"),
        ]
        for t, c, d in samples:
            self.add_document(t, c, d)
        return len(samples)
