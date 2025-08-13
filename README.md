# PDF-PARSER
# USB PD Specification PDF Parser

This project extracts structured data from the **USB Power Delivery Specification** PDF and produces machine-readable JSONL files for the Table of Contents, specification content, and document metadata.  
It also generates a validation report in Excel format.

## 📂 Outputs
After running the notebook, the following files will be created in the `output_json/` folder:

- **usb_pd_toc.jsonl** — Parsed Table of Contents with section IDs, titles, page numbers, hierarchy, and tags.
- **usb_pd_spec.jsonl** — Full section content with page ranges, number of tables, and extracted text.
- **usb_pd_metadata.jsonl** — Document metadata such as title, author, total pages, and extraction timestamp.
- **validation_report.xlsx** — Summary of parsing results with mismatch analysis.

## 🛠 Dependencies
Install required Python packages:
```bash
pip install pymupdf pdfplumber pandas openpyxl
