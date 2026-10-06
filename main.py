"""Intelligent Industrial Document Management System - PySide6 MVP.

Run:  pip install PySide6   then   python main.py
"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QStringListModel, QUrl, Qt
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QComboBox, QCompleter, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGraphicsScene, QGraphicsView, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QAbstractItemView, QHeaderView,
)

from dsa import AVLTree, DocumentBST
from manager import Document, DocumentManager

PLACEHOLDERS = [
    "Exact ID (SAF-0001) or ID prefix (SAF-) - press Enter to see the AVL search path",
    "Type words - prefix match as you type, e.g. saf insp",
    "Typo-tolerant - e.g. maintenence, safty",
]
COLUMNS = ["Doc ID", "Title", "Category", "Ver", "Status", "Uploaded"]
STYLE = """
QMainWindow, QWidget { font-size: 13px; }
QPushButton { padding: 6px 14px; border-radius: 4px; border: 1px solid #8a94a6; }
QPushButton#primary { background: #2f6fed; color: white; border: none; }
QPushButton#danger { color: #c62828; }
QTableWidget { alternate-background-color: rgba(128,128,128,0.08); }
"""


class UploadDialog(QDialog):
    def __init__(self, parent, categories: list[str], preselect: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Upload Document")
        self.setMinimumWidth(460)
        self.title = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(categories)
        if preselect in categories:
            self.category.setCurrentText(preselect)
        self.description = QTextEdit()
        self.description.setFixedHeight(70)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Optional - choose a file to store")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_edit)
        file_row.addWidget(browse)
        form = QFormLayout(self)
        form.addRow("Title *", self.title)
        form.addRow("Category *", self.category)
        form.addRow("Description", self.description)
        form.addRow("File", file_row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select document")
        if path:
            self.file_edit.setText(path)
            if not self.title.text():
                self.title.setText(os.path.splitext(os.path.basename(path))[0])

    def _accept(self):
        if not self.title.text().strip():
            QMessageBox.warning(self, "Missing title", "Please enter a title.")
            return
        self.accept()

    def values(self) -> dict:
        return dict(title=self.title.text(), category=self.category.currentText(),
                    description=self.description.toPlainText(), source_file=self.file_edit.text())


class MainWindow(QMainWindow):
    def __init__(self, manager: DocumentManager):
        super().__init__()
        self.mgr = manager
        self.current_category = ""   # "" = all documents
        self.shown: list[Document] = []
        self.setWindowTitle("Intelligent Industrial Document Management System")
        self.resize(1200, 720)
        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------- UI
    def _build_ui(self):
        # search bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(PLACEHOLDERS[0])
        self.search_edit.returnPressed.connect(self.do_search)
        self.completer_model = QStringListModel(self)
        completer = QCompleter(self.completer_model, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_edit.setCompleter(completer)
        self.mode = QComboBox()
        self.mode.addItems(["Document ID (AVL)", "Keywords (Trie prefix)", "Fuzzy (typo-tolerant)"])
        self.search_edit.textChanged.connect(self._on_text)
        self.mode.currentIndexChanged.connect(self._on_mode)
        go = QPushButton("Search")
        go.setObjectName("primary")
        go.clicked.connect(self.do_search)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_search)
        top = QHBoxLayout()
        for w in (self.search_edit, self.mode, go, clear):
            top.addWidget(w)
        top.setStretch(0, 1)

        # category tree
        self.cat_tree = QTreeWidget()
        self.cat_tree.setHeaderLabel("Categories")
        self.cat_tree.itemSelectionChanged.connect(self.on_category_changed)
        add_cat = QPushButton("+ Category")
        add_cat.clicked.connect(self.add_category)
        rm_cat = QPushButton("Remove")
        rm_cat.clicked.connect(self.remove_category)
        cat_btns = QHBoxLayout()
        cat_btns.addWidget(add_cat)
        cat_btns.addWidget(rm_cat)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(self.cat_tree)
        lv.addLayout(cat_btns)

        # documents tab
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.on_row_changed)
        self.table.doubleClicked.connect(self.open_file)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setFixedHeight(100)
        up = QPushButton("Upload Document")
        up.setObjectName("primary")
        up.clicked.connect(self.upload)
        self.open_btn = QPushButton("Open File")
        self.open_btn.clicked.connect(self.open_file)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("danger")
        self.del_btn.clicked.connect(self.delete)
        btns = QHBoxLayout()
        for b in (up, self.open_btn, self.del_btn):
            btns.addWidget(b)
        btns.addStretch()
        docs_tab = QWidget()
        dv = QVBoxLayout(docs_tab)
        dv.addLayout(btns)
        dv.addWidget(self.table)
        dv.addWidget(self.details)

        # BST visualizer tab
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QBrush(QColor("#ffffff")))
        self.path_label = QLabel("Search by Document ID to see the comparison path highlighted here.")
        self.path_label.setWordWrap(True)
        viz_tab = QWidget()
        vv = QVBoxLayout(viz_tab)
        vv.addWidget(self.path_label)
        vv.addWidget(self.view)

        self.tabs = QTabWidget()
        self.tabs.addTab(docs_tab, "Documents")
        self.tabs.addTab(viz_tab, "AVL Index Visualizer")

        split = QSplitter()
        split.addWidget(left)
        split.addWidget(self.tabs)
        split.setStretchFactor(1, 1)
        split.setSizes([260, 940])

        central = QWidget()
        cv = QVBoxLayout(central)
        cv.addLayout(top)
        cv.addWidget(split)
        self.setCentralWidget(central)

        menu = self.menuBar().addMenu("&File")
        menu.addAction("Load sample data", self.load_samples)
        menu.addAction("AVL vs plain BST demo", self.balance_demo)
        menu.addSeparator()
        menu.addAction("Quit", self.close)
        self.setStyleSheet(STYLE)

    # -------------------------------------------------------------- refresh
    def refresh_all(self):
        self.refresh_categories()
        self.show_docs(self.docs_for_current_category())
        self.redraw_bst()

    def docs_for_current_category(self) -> list[Document]:
        if not self.current_category:
            return self.mgr.all_documents()
        return self.mgr.by_category(self.current_category)

    def refresh_categories(self):
        self.cat_tree.blockSignals(True)
        self.cat_tree.clear()

        def add(node, parent_item):
            count = len(self.mgr.tree.subtree_doc_ids(node))
            item = QTreeWidgetItem(parent_item, [f"{node.name} ({count})"])
            item.setData(0, Qt.UserRole, node.path())
            for c in node.children:
                add(c, item)
            return item

        root = add(self.mgr.tree.root, self.cat_tree.invisibleRootItem())
        self.cat_tree.expandAll()
        target = root
        it = self.cat_tree.findItems("*", Qt.MatchWildcard | Qt.MatchRecursive)
        for item in it:
            if item.data(0, Qt.UserRole) == self.current_category:
                target = item
        self.cat_tree.setCurrentItem(target)
        self.cat_tree.blockSignals(False)

    def show_docs(self, docs: list[Document]):
        self.shown = docs
        self.table.setRowCount(len(docs))
        for r, d in enumerate(docs):
            vals = [d.doc_id, d.title, d.category, f"v{d.version}", d.status, d.uploaded_at]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if d.status == "Superseded":
                    item.setForeground(QBrush(QColor("#9e9e9e")))
                self.table.setItem(r, c, item)
        self.details.clear()
        self.update_status()

    def update_status(self, extra: str = ""):
        n = len(self.mgr.bst)
        msg = f"{n} documents indexed | AVL height: {self.mgr.bst.height()} | rotations: {self.mgr.bst.rotations} | showing {len(self.shown)}"
        self.statusBar().showMessage(msg + (f" | {extra}" if extra else ""))

    def selected_doc(self) -> Document | None:
        row = self.table.currentRow()
        return self.shown[row] if 0 <= row < len(self.shown) else None

    # -------------------------------------------------------------- events
    def on_category_changed(self):
        items = self.cat_tree.selectedItems()
        self.current_category = items[0].data(0, Qt.UserRole) if items else ""
        self.search_edit.clear()
        self.show_docs(self.docs_for_current_category())

    def on_row_changed(self):
        d = self.selected_doc()
        if not d:
            return
        self.details.setPlainText(
            f"{d.doc_id}  -  {d.title}  (v{d.version}, {d.status})\n"
            f"Category: {d.category}\nUploaded: {d.uploaded_at}\n"
            f"File: {d.file_path or '(none attached)'}\n\n{d.description}")
        self.open_btn.setEnabled(bool(d.file_path))

    def do_search(self):
        text = self.search_edit.text().strip()
        if not text:
            return self.clear_search()
        if self.mode.currentIndex() == 0:
            docs, path = self.mgr.search_id(text)
            found = docs[0].doc_id if len(docs) == 1 and docs[0].doc_id == text.upper() else None
            self.redraw_bst(path, found)
            trail = " -> ".join(path) if path else "(tree empty)"
            outcome = "FOUND" if found else f"{len(docs)} prefix match(es)"
            self.path_label.setText(f"Search '{text.upper()}': {outcome} after {len(path)} comparison(s).  Path: {trail}")
            self.show_docs(docs)
            self.update_status(f"{len(path)} comparisons")
        else:
            fuzzy = self.mode.currentIndex() == 2
            self.show_docs(self.mgr.search_text(text, fuzzy=fuzzy))
            fixes = self.mgr.corrections(text) if fuzzy else []
            if fixes:
                self.update_status("Did you mean: " + ", ".join(f"{a} -> {b}" for a, b in fixes))

    def _on_text(self, text: str):
        mode = self.mode.currentIndex()
        self.completer_model.setStringList(self.mgr.autocomplete(text) if mode else [])
        if not text.strip():
            self.clear_search()
        elif mode:                      # live search-as-you-type for Trie / fuzzy modes
            self.do_search()

    def _on_mode(self, index: int):
        self.search_edit.setPlaceholderText(PLACEHOLDERS[index])
        self._on_text(self.search_edit.text())

    def balance_demo(self):
        n, bst, avl = 200, DocumentBST(), AVLTree()
        for i in range(n):              # sorted inserts = worst case for a plain BST
            bst.insert(f"DOC-{i:04d}", i)
            avl.insert(f"DOC-{i:04d}", i)
        QMessageBox.information(
            self, "AVL vs plain BST",
            f"Inserting {n} IDs in sorted order (worst case):\n\n"
            f"Plain BST height: {bst.height()}  ->  up to {bst.height()} comparisons per search\n"
            f"AVL tree height: {avl.height()}  ->  at most {avl.height()} comparisons "
            f"({avl.rotations} rotations)")

    def clear_search(self):
        self.search_edit.clear()
        self.path_label.setText("Search by Document ID to see the comparison path highlighted here.")
        self.redraw_bst()
        self.show_docs(self.docs_for_current_category())

    def upload(self):
        dlg = UploadDialog(self, self.mgr.category_paths(), self.current_category)
        if dlg.exec() != QDialog.Accepted:
            return
        try:
            doc = self.mgr.add_document(**dlg.values())
        except (ValueError, OSError) as e:
            return QMessageBox.critical(self, "Upload failed", str(e))
        self.refresh_all()
        self.update_status(f"added {doc.doc_id}")

    def open_file(self):
        d = self.selected_doc()
        if d and d.file_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(d.file_path))

    def delete(self):
        d = self.selected_doc()
        if not d:
            return QMessageBox.information(self, "Delete", "Select a document first.")
        if QMessageBox.question(self, "Delete", f"Delete {d.doc_id} - {d.title}?") != QMessageBox.Yes:
            return
        self.mgr.delete_document(d.doc_id)
        self.refresh_all()
        self.update_status(f"deleted {d.doc_id}")

    def add_category(self):
        name, ok = QInputDialog.getText(self, "New category", f"Name (under '{self.current_category or 'All Documents'}'):")
        if ok:
            try:
                self.mgr.add_category(self.current_category, name)
            except ValueError as e:
                return QMessageBox.warning(self, "Category", str(e))
            self.refresh_categories()

    def remove_category(self):
        try:
            self.mgr.remove_category(self.current_category)
        except ValueError as e:
            return QMessageBox.warning(self, "Category", str(e))
        self.current_category = ""
        self.refresh_all()

    def load_samples(self):
        if len(self.mgr.bst):
            return QMessageBox.information(self, "Samples", "Sample data can only be loaded into an empty index.")
        n = self.mgr.load_samples()
        self.refresh_all()
        self.update_status(f"loaded {n} sample documents")

    # ------------------------------------------------------- BST visualizer
    def redraw_bst(self, path=(), found=None):
        self.scene.clear()
        bst = self.mgr.bst
        if len(bst) == 0:
            self.scene.addText("Index is empty - upload a document or load sample data.")
            return
        if len(bst) > 150:
            self.scene.addText(f"{len(bst)} nodes - too many to draw (limit 150).")
            return
        w, h, gx, gy = 96, 30, 108, 80
        pos = {k: (i * gx, d * gy) for k, d, i, _ in bst.layout()}
        for k, _, _, p in bst.layout():
            if p is not None:
                on_path = k in path and p in path
                pen = QPen(QColor("#f2a900" if on_path else "#90a4ae"), 3 if on_path else 1.5)
                self.scene.addLine(pos[p][0] + w / 2, pos[p][1] + h, pos[k][0] + w / 2, pos[k][1], pen)
        for k, (x, y) in pos.items():
            color = "#66bb6a" if k == found else "#ffd54f" if k in path else "#bbdefb"
            shape = QPainterPath()
            shape.addRoundedRect(x, y, w, h, 8, 8)
            self.scene.addPath(shape, QPen(QColor("#455a64")), QBrush(QColor(color)))
            label = self.scene.addText(k)
            label.setDefaultTextColor(QColor("#1b1b1b"))
            label.setPos(x + (w - label.boundingRect().width()) / 2, y + (h - label.boundingRect().height()) / 2)
        target = found or (path[-1] if path else None)
        if target in pos:
            self.view.centerOn(pos[target][0] + w / 2, pos[target][1] + h / 2)


def main():
    app = QApplication(sys.argv)
    win = MainWindow(DocumentManager())
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
