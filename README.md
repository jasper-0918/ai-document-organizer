# 📁 AI Document Organizer — Stop Filing. Let AI Do It.

> **Automatically sorts every file in your computer into the right folder — using AI. Zero manual effort.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Transformers](https://img.shields.io/badge/HuggingFace-Transformers-yellow?logo=huggingface)](https://huggingface.co)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9%2B-green?logo=opencv)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

---

## 😩 The Problem This Solves

Does your Downloads folder look like this?

```
Downloads/
├── invoice_march.pdf
├── john_doe_cv.docx
├── screenshot_2024-03-15.png
├── receipt_lazada.pdf
├── random_file.pdf
├── my_photo.jpg
├── contract_draft_v3.docx
└── 47 more files...
```

Every week, files pile up. Finding what you need takes longer and longer.

For virtual assistants managing files for clients, this gets out of hand fast.

**The AI Document Organizer watches your folder and sorts everything automatically — while you work on something else.**

---

## ✅ What It Does

Drop files into a watched folder. The AI reads or analyzes each one and moves it to the right place — automatically, on a schedule, forever.

**Before:**
```
inbox/  ← dumping ground of chaos
├── invoice_march.pdf
├── john_doe_cv.docx
├── vacation_photo.jpg
├── error_screenshot.png
└── contract_v3.docx
```

**After (organized automatically):**
```
organized/
├── invoice/2024-06/
│   └── invoice_march.pdf
├── resume/2024-06/
│   └── john_doe_cv.docx
├── photo/2024-06/
│   └── vacation_photo.jpg
├── screenshot/2024-06/
│   └── error_screenshot.png
└── contract/2024-06/
    └── contract_v3.docx
```

**Zero manual sorting. Zero duplicates. Everything in the right place.**

---

## 📈 Results

- **Eliminates manual file sorting** — set it once, it runs forever on a schedule
- **Never creates duplicate files** — built-in duplicate detection using image fingerprinting
- **Handles mixed file types** — PDFs, Word docs, images, spreadsheets, presentations, text files
- **Skips already-processed files** — won't re-sort what's already been sorted
- **Preview before it moves anything** — dry-run mode shows what will happen first

---

## 💼 Who This Is For

This tool is perfect for:

- **Virtual assistants** managing file downloads and documents for multiple clients
- **Remote workers** whose Downloads folder is out of control
- **Small business owners** who need invoices, contracts, and receipts auto-organized
- **Freelancers** juggling documents across multiple projects and clients

> **You don't need to touch the code.** Edit one settings file, run one command, done.

---

## 🎬 Demo

> 📽️ **Full demo video coming soon** — will show the tool classifying and sorting mixed files in real time.

[![▶ Watch Demo — AI Document Organizer](https://img.shields.io/badge/▶%20Watch%20Demo-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

<!--
WHEN YOUR VIDEO IS READY — replace the shield above with this clickable thumbnail instead:

[![Watch the demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

That will render as a clickable screenshot thumbnail directly from your YouTube video.
-->

---

## ⚙️ How It Works — Plain English

```
File drops into your watched folder
│
▼
Is it a document? (PDF, Word, Excel, text...)
  → AI reads the content
  → Classifies it: invoice / resume / contract / report / etc.
│
Is it an image? (JPG, PNG...)
  → AI analyzes visual patterns
  → Classifies it: photo / screenshot / diagram / scan
│
▼
Is this a duplicate of a file already organized?
  → YES → Skip it, don't create a copy
  → NO  → Move to organized/<category>/<year-month>/
│
▼
Log it in the database → Next scan, this file is skipped automatically
```

---

## 🗂️ Categories It Understands

The AI can classify files into any of these categories — or you can add your own:

`invoice` · `resume` · `contract` · `report` · `receipt` · `photo` · `screenshot` · `diagram` · `document scan` · `spreadsheet` · `presentation` · `unknown`

---

## 🚀 Setup (Under 10 Minutes)

### Step 1 — Install

```bash
git clone https://github.com/jasper-0918/ai-document-organizer.git
cd ai-document-organizer
pip install -r requirements.txt
```

> First run downloads the AI model automatically (~1.6 GB). This happens once.

---

### Step 2 — Configure

Open `config.yaml` and set your folders:

```yaml
target_folder: "./inbox"      # ← folder to watch (drop files here)
output_folder: "./organized"  # ← where sorted files go

schedule:
  interval_minutes: 5         # ← how often to scan (with --watch mode)
```

---

### Step 3 — Drop files and run

```bash
# Sort everything in the inbox folder right now
python main.py

# Preview what WILL happen without moving anything (safe to try first)
python main.py --dry-run

# Keep watching and sorting every 5 minutes automatically
python main.py --watch

# Sort a specific folder (e.g. your Downloads)
python main.py --folder ~/Downloads
```

---

## 🔁 Automation Options

**One-time sort** — run it manually whenever you want to clean up:
```bash
python main.py
```

**Continuous auto-sort** — runs in the background, sorts every 5 minutes:
```bash
python main.py --watch
```

**Dry run first** — always recommended before first use, so you can see what it plans to do:
```bash
python main.py --dry-run
```

---

## 🛡️ Smart Features

**Duplicate prevention** — uses perceptual hashing to detect identical images even if they're renamed. Will never sort the same file twice.

**History database** — every processed file is logged. Re-running never touches files that were already sorted.

**Unknown category** — files the AI isn't confident about go into `organized/unknown/` instead of being misplaced. You review those manually.

**Dry-run mode** — see exactly what would move where, without moving anything. Test before committing.

---

## ⚠️ Honest Limitations

- **First run is slow** — the AI model (~1.6 GB) downloads on first use. After that, it loads from your computer.
- **Accuracy isn't 100%** — unusual or ambiguous files may land in `unknown/` for you to sort manually.
- **Local only** — runs on your computer, not in the cloud. Files never leave your machine.
- **Text-heavy files work best** — PDFs and Word docs get better accuracy than generic images.

---

## 🔒 Your Files Stay Private

The AI model runs entirely on your own computer. **No files are uploaded to any cloud service, no data is sent to any external server.**

---

## 🛠️ Technical Details

<details>
<summary>Click to expand — for the technically curious</summary>

**AI Models Used:**
- Text classification: `facebook/bart-large-mnli` (zero-shot, no training data needed)
- Image analysis: OpenCV heuristics (edge density, color entropy, aspect ratio)
- Duplicate detection: Perceptual hashing (pHash)

**Supported File Types:**
- Documents: `.pdf`, `.docx`, `.txt`, `.xlsx`, `.pptx`
- Images: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.webp`

**Tech Stack:**
- Python 3.11+
- HuggingFace Transformers
- OpenCV 4.9+
- SQLite (history database)
- schedule (periodic scanning)
- pdfplumber, python-docx, python-pptx, openpyxl (document parsing)

</details>

---

## 📬 Want This Built for Your Business?

If you have **repetitive file management or workflow tasks** that need automation, I can build a custom solution for you — tailored to your specific folder structure, file types, and business needs.

I specialize in Python automation for businesses and virtual assistants.

👉 **[Connect on LinkedIn](https://www.linkedin.com/in/jasper-john-paitan-11641337b)**
📧 **jasper.paitan0918@gmail.com**
🏅 **[View Certifications](https://www.credly.com/users/jasper-john-paitan)**

---

## 📄 License

MIT — free to use and modify.
