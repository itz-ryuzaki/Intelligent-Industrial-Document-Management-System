# 🏭 Intelligent Industrial Document Management System

> 📂 A desktop application for organising, indexing and retrieving industrial documents using **tree, graph, dynamic programming, and advanced data structures**, built with **Python** and **PySide6**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)
![Course](https://img.shields.io/badge/Course-DSA%20II-orange)
![SDG](https://img.shields.io/badge/SDG-9%20Industry%2C%20Innovation%20%26%20Infrastructure-F36D25)
![Status](https://img.shields.io/badge/Status-Academic%20Project-lightgrey)

---

## 📖 Table of Contents

- [🎯 Overview](#-overview)
- [❗ The Problem](#-the-problem)
- [✨ Key Features](#-key-features)
- [🧠 Data Structures & Algorithms Used](#-data-structures--algorithms-used)
- [🏗️ System Architecture](#️-system-architecture)
- [🖥️ Screenshots](#️-screenshots)
- [📁 Project Structure](#-project-structure)
- [⚙️ Installation](#️-installation)
- [🚀 Usage Guide](#-usage-guide)
- [⏱️ Complexity Analysis](#️-complexity-analysis)
- [🧪 Testing](#-testing)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📚 References](#-references)
- [👤 Author](#-author)
- [📄 License](#-license)

---

## 🎯 Overview

Industrial organisations handle large volumes of **safety manuals, maintenance records, quality-control reports, inspection documents and operating procedures**. When these are stored without structure, finding the right document is slow and teams risk using outdated versions.

This project provides a structured platform that:

- 🗂️ Organises documents into a **category tree** of categories and sub-categories
- 🔍 Indexes records with an **AVL tree** for fast lookup by document ID
- ⌨️ Supports **prefix search and autocomplete** via a **Trie**
- ✏️ Tolerates **typos** in search terms
- 🔗 Models **relationships** between documents as a graph
- 💾 Optimises **storage** and compares **document versions**
- 📊 Shows the **AVL search path** in a visualiser so users can see how indexing works

It is built as an academic project for **Data Structures and Algorithms II**, and aligns with **SDG 9: Industry, Innovation and Infrastructure**.

---

## ❗ The Problem

| 😩 Challenge | 💡 How this project addresses it |
|---|---|
| No consistent document hierarchy | 🌳 Category tree with categories and sub-categories |
| Slow lookup by ID or name | ⚡ AVL tree index, O(log n) search |
| Hard-to-find documents from partial names | 🔤 Trie-based prefix search and autocomplete |
| Spelling mistakes return nothing | ✏️ Typo-tolerant search |
| Hidden dependencies between documents | 🕸️ Document graph with BFS, DFS and Dijkstra |
| Limited storage for archives | 🎒 0/1 Knapsack selection by importance |
| Hard to see what changed between versions | 📝 LCS-based version comparison with similarity % |
| Documents need prioritising | 🚦 Max-heap priority queue and Heap Sort |

---

## ✨ Key Features

### 📄 Document Management
- ➕ **Add documents** with title, category, metadata and an attached file
- 🏷️ **Assign categories** from the hierarchical category tree
- 📋 **View document details** and metadata
- 🗑️ **Delete records** safely from the index
- 📑 **Sorted listing** of documents via in-order traversal

### 🔎 Multi-Mode Search
- 🆔 **Search by ID**: AVL tree lookup
- 🔡 **Keyword search**: Trie-based prefix matching
- 💬 **Autocomplete** while typing
- 🩹 **Typo-tolerant search** for misspelt terms

### 🧩 Intelligence & Analysis
- 🔗 **Relationship management**: `RELATED_TO`, `DEPENDS_ON`, `REFERENCES` edges
- 🧭 **Dependency exploration**: BFS (related documents) and DFS (dependency chains)
- 🛣️ **Shortest dependency path** with Dijkstra
- 🥇 **Prioritisation** with a max-heap and Heap Sort
- 📦 **Storage optimisation** with 0/1 Knapsack
- 🔀 **Version comparison** with Longest Common Subsequence

### 🎨 Interface
- 🖥️ Desktop GUI built with **PySide6**
- 🌲 **AVL visualiser** showing the search path through the index

---

## 🧠 Data Structures & Algorithms Used

| Unit | Topic | Where it's used | Complexity |
|:---:|---|---|---|
| 🌳 **1** | AVL Tree (self-balancing BST) | Document ID index | Search / Insert / Delete: **O(log n)** |
| 🌳 **1** | Category Tree | Document hierarchy | Traversal: **O(n)** |
| 🌳 **1** | Trie | Prefix search and autocomplete | **O(L + k)** |
| 🌳 **1** | Binary Max-Heap | Priority queue | Insert / Extract: **O(log n)** |
| 🌳 **1** | Heap Sort | Priority-ordered reports | **O(n log n)** |
| 🕸️ **2** | Adjacency List | Document relationship graph | **O(V + E)** space |
| 🕸️ **2** | BFS | Find related documents | **O(V + E)** |
| 🕸️ **2** | DFS | Dependency chain explorer | **O(V + E)** |
| 🕸️ **2** | Dijkstra | Shortest dependency path | **O((V + E) log V)** |
| 🧮 **3** | 0/1 Knapsack | Storage optimisation | **O(nW)** |
| 🧮 **3** | Longest Common Subsequence | Version comparison | **O(mn)** |
| 🧮 **3** | Edit distance (Wagner–Fischer) | Typo-tolerant matching | **O(mn)** |
| 🔁 **4** | Backtracking / Branch & Bound | *Planned*: Sum of Subsets, Graph Colouring | Exponential (see report) |
| 🏛️ **5** | B+ Tree | *Recommended* for disk-based persistent index | **O(log_t n)** |

> 📘 The full analysis, including comparison tables and diagrams, is in the project report.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│  🖥️  Presentation Layer (PySide6 GUI)        │
│     Upload · Search · View · Delete · AVL 🌲 │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│  🧭  Service Layer (Document Manager)        │
│     Coordinates operations, validates input  │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│  🧠  DSA Modules (one per algorithm)         │
│  AVL · Trie · Category Tree · Heap ·         │
│  Graph (BFS/DFS/Dijkstra) · Knapsack · LCS   │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│  💾  Storage (document files + metadata)     │
└─────────────────────────────────────────────┘
```

**Design principles**

- 🧱 **Separation of concerns:** algorithms are independent of the GUI and tested in isolation.
- 🎯 **Right structure per feature:** each operation uses the structure with the best complexity for it.
- 🔌 **Replaceable index:** the service layer depends on an index abstraction, so the AVL index can later move to a B+ tree.

---

## 🖥️ Screenshots

> 📸 *Add screenshots to a `docs/screenshots/` folder and link them here.*

| 🏠 Main Window | 🔍 Search | 🌲 AVL Visualiser |
|:---:|:---:|:---:|
| `docs/screenshots/main.png` | `docs/screenshots/search.png` | `docs/screenshots/avl.png` |

---

## 📁 Project Structure

```
Intelligent-Industrial-Document-Management-System/
│
├── 📄 main.py                  # Application entry point
├── 📂 gui/                     # PySide6 windows, dialogs and widgets
├── 🧠 dsa/                     # Core algorithm modules
│   ├── avl_tree.py             # AVL index + visualiser data
│   ├── category_tree.py        # Hierarchical category tree
│   ├── trie.py                 # Prefix search and autocomplete
│   ├── heap.py                 # Max-heap, priority queue, heap sort
│   ├── graph.py                # Adjacency list, BFS, DFS
│   ├── dijkstra.py             # Shortest dependency path
│   ├── knapsack.py             # 0/1 storage optimisation
│   └── lcs.py                  # Version comparison
├── ⚙️ services/                # Document Manager (service layer)
├── 💾 storage/                 # File and metadata storage
├── 🧪 tests/                   # Unit tests (normal, empty, edge cases)
├── 📚 docs/                    # Report, diagrams, screenshots
├── 📋 requirements.txt         # Python dependencies
└── 📖 README.md
```

> ⚠️ *Adjust the file and folder names above to match the actual repository.*

---

## ⚙️ Installation

### ✅ Prerequisites

- 🐍 **Python 3.10 or newer**
- 📦 **pip**
- 🪟 / 🐧 / 🍎 Windows, Linux or macOS

### 🛠️ Steps

```bash
# 1️⃣ Clone the repository
git clone https://github.com/itz-ryuzaki/Intelligent-Industrial-Document-Management-System.git
cd Intelligent-Industrial-Document-Management-System

# 2️⃣ Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3️⃣ Install dependencies
pip install -r requirements.txt
# or, if no requirements file is present:
pip install PySide6

# 4️⃣ Run the application
python main.py
```

---

## 🚀 Usage Guide

### ➕ Adding a Document
1. Click **Add Document**
2. Enter the title and metadata
3. Choose a category from the tree 🌳
4. Attach the file 📎
5. Save ✅

### 🔎 Searching
| Mode | How to use | Engine |
|---|---|---|
| 🆔 By ID | Type the document ID | AVL tree |
| 🔡 By keyword | Type a word or prefix | Trie |
| ✏️ Typo-tolerant | Type a misspelt term | Edit-distance matching |

### 🔗 Relationships & Analysis
- ➡️ Create a link between two documents: `RELATED_TO`, `DEPENDS_ON` or `REFERENCES`
- 🧭 Run **BFS** to list related documents
- 🔗 Run **DFS** to explore a dependency chain
- 🛣️ Run **Dijkstra** to find the cheapest dependency path (non-negative weights only)
- 📦 Run **Knapsack** with a storage limit to choose the most important documents
- 🔀 Run **LCS** to compare two versions and get a similarity percentage

### 🌲 AVL Visualiser
Select a document ID and open the visualiser to see the path taken through the index. Useful for understanding how tree-based indexing works.

---

## ⏱️ Complexity Analysis

| 🔧 Operation | ⏱️ Time | 💾 Space |
|---|---|---|
| AVL search / insert / delete | O(log n) | O(n) |
| Trie prefix search | O(L + k) | O(total characters) |
| Heap insert / extract | O(log n) | O(n) |
| Heap Sort | O(n log n) | O(1) extra |
| BFS / DFS | O(V + E) | O(V) |
| Dijkstra (binary heap) | O((V + E) log V) | O(V + E) |
| 0/1 Knapsack | O(nW) | O(nW) or O(W) |
| LCS | O(mn) | O(mn) |

> 🔑 **Legend:** `n` = documents · `V` = vertices · `E` = edges · `L` = prefix length · `k` = matches · `W` = storage capacity · `m, n` = lengths of two sequences

---

## 🧪 Testing

Each algorithm is tested independently, including the edge cases that matter most:

- 🫙 **Empty** inputs (empty heap, empty graph)
- 1️⃣ **Single element** inputs
- 🚫 **Unreachable** destinations in Dijkstra
- 0️⃣ **Zero** storage limit in Knapsack
- ⚖️ **Equal** priorities in the heap

```bash
python -m pytest tests/ -v
```

---

## 🗺️ Roadmap

- [x] 🌳 Category tree and AVL index
- [x] ⌨️ Trie search and autocomplete
- [x] 🕸️ Document graph with BFS, DFS and Dijkstra
- [x] 📦 Knapsack and LCS optimisation modules
- [x] 🥇 Max-heap and Heap Sort
- [ ] 🔁 Backtracking and Branch & Bound features (Sum of Subsets / Graph Colouring)
- [ ] 💾 Persistent B+ tree index for large archives
- [ ] 🤖 **AI chatbot using Retrieval-Augmented Generation (RAG)** to answer natural-language questions about stored documents
- [ ] 📊 Benchmarks at several collection sizes to validate complexity claims

---

## 🤝 Contributing

Contributions, suggestions and bug reports are welcome!

1. 🍴 Fork the repository
2. 🌿 Create a feature branch: `git checkout -b feature/your-feature`
3. 💬 Commit your changes: `git commit -m "Add your feature"`
4. 📤 Push to the branch: `git push origin feature/your-feature`
5. 🔃 Open a Pull Request

Please keep algorithm modules independent of the GUI and add tests for normal and edge-case inputs.

---

## 📚 References

- 📖 Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. *Introduction to Algorithms* (4th ed.). MIT Press.
- 📄 Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*.
- 📄 Hunt, J. W., & Szymanski, T. G. (1977). A fast algorithm for computing longest common subsequences. *CACM*.
- 📄 Wagner, R. A., & Fischer, M. J. (1974). The string-to-string correction problem. *JACM*.
- 📄 Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *arXiv*.

---

## 👤 Author

**Swayam Yadav** 🎓
B.Tech (AI/AIML), NIET Greater Noida
Course: Data Structures and Algorithms II (BCSE0401)

---

## 📄 License

🔒 This project is an academic submission. Add a license file (for example MIT) before reusing the code.

---

<p align="center">
  ⭐ If you found this project useful, consider giving it a star! ⭐<br>
  Made with 🐍 Python, 🎨 PySide6 and 🌳 lots of data structures.
</p>
