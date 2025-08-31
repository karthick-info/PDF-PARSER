# USB PD Specification PDF Parser

This project extracts structured data from the **USB Power Delivery Specification** PDF and produces machine-readable JSONL files for the Table of Contents, specification content, and document metadata. It also generates a validation report in Excel format.

## ✨ Key Features
- **Automated TOC Detection**: Scans PDFs for table of contents entries using regex patterns
- **Hierarchical Section Parsing**: Processes nested section structures with proper parent-child relationships
- **Content Extraction**: Retrieves full text content for each section between defined boundaries
- **Validation Reporting**: Compares TOC entries with extracted content and generates Excel reports
- **JSONL Output**: Saves structured data in newline-delimited JSON format for easy processing

## 📂 Outputs
After running the script, the following files will be created in the `output_json/` folder:
- **`usb_pd_toc.jsonl`** — Parsed Table of Contents with section IDs, titles, page numbers, hierarchy levels, and tags
- **`usb_pd_spec.jsonl`** — Full section content with metadata from TOC
- **`usb_pd_metadata.jsonl`** — Document metadata (title, author, total pages, extraction timestamp)
- **`validation_report.xlsx`** — Excel report comparing TOC entries vs. extracted content with mismatch analysis

## 🛠 Dependencies
Install required Python packages:
```bash
pip install -r requirements.txt
```

## 🔧 Usage
1. Place your USB PD specification PDF in the project directory
2. Run the main script:
   ```bash
   python main.py
   ```
3. Check the `output_json/` folder for generated files

## ⚙️ Configuration
Modify these variables in `main.py` to customize behavior:
```python
PDF_PATH = "USB_PD_R3_2 V1.1 2024-10.pdf"  # Path to your PDF
OUTPUT_DIR = "output_json"                  # Output directory name
```

## 💻 Example Output Structure
```json
{
  "doc_title": "Universal Serial Bus Power Delivery Specification",
  "section_id": "1",
  "title": "Introduction",
  "page": 1,
  "level": 1,
  "parent_id": null,
  "full_path": "1 Introduction",
  "tags": [],
  "content": "This document specifies the Universal Serial Bus Power Delivery standard..."
}
```

