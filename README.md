# 🤖 AI Document Organizer

> Automatically sort files in a folder using NLP and computer vision.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![Transformers](https://img.shields.io/badge/HuggingFace-Transformers-yellow?logo=huggingface)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9%2B-green?logo=opencv)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## ✨ Features

| Feature | Details |
|---|---|
| **NLP classification** | Zero-shot text classification via `facebook/bart-large-mnli` — no labelled data needed |
| **Image recognition** | OpenCV heuristics (edge density, color entropy, aspect ratio) to label screenshots, photos, diagrams, and document scans |
| **Duplicate detection** | Perceptual hashing (pHash) prevents identical images from being copied twice |
| **SQLite history** | Every scan is logged; already-processed files are skipped on the next run |
| **Scheduled watching** | `--watch` flag keeps the process alive and rescans every N minutes |
| **Dry-run mode** | Preview what *would* happen without touching any files |

---

## 📁 Output Structure

Files are moved into:

```
organized/
├── invoice/
│   └── 2024-06/
│       └── Q2_invoice.pdf
├── resume/
│   └── 2024-06/
│       └── john_doe_cv.docx
├── photo/
│   └── 2024-06/
│       └── vacation.jpg
├── screenshot/
│   └── 2024-06/
│       └── error_msg.png
└── unknown/
    └── 2024-06/
        └── mystery_file.bin
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/yourusername/ai-doc-organizer.git
cd ai-doc-organizer

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

> **CPU-only PyTorch** (lighter install):
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> ```

### 2. Configure

Edit `config.yaml`:

```yaml
target_folder: "./inbox"      # folder to scan
output_folder: "./organized"  # where sorted files land
schedule:
  interval_minutes: 5         # used with --watch
```

### 3. Drop some files into `inbox/` and run

```bash
# One-time scan
python main.py

# Preview without moving anything
python main.py --dry-run

# Keep watching every 5 minutes
python main.py --watch

# Point at a different folder
python main.py --folder ~/Downloads
```

---

## ⚙️ How It Works

```
File detected
    │
    ├─ Text file? (.pdf, .docx, .txt …)
    │       │
    │       └─▶ Extract text (pdfplumber / python-docx / plain read)
    │                   │
    │                   └─▶ HuggingFace zero-shot classification
    │                               │
    │                               └─▶ label + confidence score
    │
    └─ Image file? (.jpg, .png …)
            │
            └─▶ OpenCV heuristics
            │       • edge density  → diagram / document_scan
            │       • color entropy → photo / screenshot
            │       • aspect ratio  → screenshot
            │
            └─▶ pHash duplicate check
                        │
                        └─▶ label
    │
    ▼
SQLite upsert  →  move to organized/<label>/<YYYY-MM>/
```

---

## 🧪 Tests

```bash
pytest tests/ -v --cov=organizer
```

The test suite uses mocks for the HuggingFace pipeline so **no model download is required** to run tests.

---

## 🛠 Tech Stack

- **Python 3.11+**
- **[Transformers](https://github.com/huggingface/transformers)** — `facebook/bart-large-mnli` for zero-shot NLP
- **[OpenCV](https://opencv.org/)** — image analysis
- **[SQLite](https://www.sqlite.org/)** — scan history & deduplication
- **[schedule](https://github.com/dbader/schedule)** — periodic scanning
- **[pdfplumber](https://github.com/jsvine/pdfplumber)**, **python-docx**, **python-pptx**, **openpyxl** — document parsing

---

## 📄 License

MIT — see [LICENSE](LICENSE).
