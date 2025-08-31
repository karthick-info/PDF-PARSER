# -*- coding: utf-8 -*-
"""
USB Power Delivery (USB PD) Specification Parsing and Structuring System.
This script parses a USB Power Delivery specification PDF, extracts the
Table of Contents (ToC) and section content, and generates structured JSONL
files and a validation report.
"""
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
import pandas as pd

# --- CONFIGURATION ---
PDF_PATH = "USB_PD_R3_2 V1.1 2024-10.pdf"
OUTPUT_DIR = "output_fixed"

# Precompiled regex patterns for efficiency
TOC_ENTRY_PATTERN = re.compile(
    r"^(?P<section_id>(\d+(\.\d+)*)|([A-Za-z][\w\s]*))\s+"
    r"(?P<title>[^\.]{3,})\s+"
    r"(?P<page>\d+)\s*$"
)

FIGURE_TABLE_PATTERN = re.compile(r"\b(Figure|Table)\s+\d+", re.IGNORECASE)

# --- CORE FUNCTIONS ---

def extract_text_from_pdf(pdf_path: str) -> List[str]:
    """Extract text from each page of the PDF with comprehensive error handling."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    try:
        with fitz.open(pdf_path) as doc:
            return [page.get_text("text") for page in doc]
    except Exception as e:
        raise IOError(f"Error opening or reading PDF file: {e}") from e

def find_toc_content(text_pages: List[str]) -> List[str]:
    """Find Table of Contents content by scanning for numbered section formats."""
    print("🔍 Scanning for Table of Contents content...")
    toc_lines = []
    
    # Scan through all pages looking for numbered section formats
    for i, text in enumerate(text_pages):
        # Look for lines that match our TOC entry pattern
        for line in text.split('\n'):
            if TOC_ENTRY_PATTERN.match(line.strip()):
                toc_lines.append((i, line.strip()))
    
    if not toc_lines:
        raise RuntimeError("Could not find Table of Contents content in the document.")
        
    return toc_lines

def parse_toc_entries(toc_lines: List[Tuple[int, str]], doc_title: str) -> List[Dict[str, Any]]:
    """Parse TOC entries from the found content."""
    print("⚙️ Parsing Table of Contents...")
    toc_entries = []
    
    for page_num, line in toc_lines:
        entry = parse_toc_entry(line, doc_title)
        if entry:
            entry['page'] = page_num + 1  # Convert to 1-based page numbering
            toc_entries.append(entry)
    
    print(f"Found {len(toc_entries)} entries in TOC.")
    return toc_entries

def parse_toc_entry(line: str, doc_title: str) -> Optional[Dict[str, Any]]:
    """Parse a single TOC entry line into structured data."""
    match = TOC_ENTRY_PATTERN.match(line.strip())
    if not match:
        return None
        
    section_id = match.group("section_id").strip()
    title = match.group("title").strip()
    page = int(match.group("page").strip())
    
    # Determine hierarchy level and parent ID
    if re.match(r"^\d+(\.\d+)*$", section_id):
        parts = section_id.split(".")
        level = len(parts)
        parent_id = ".".join(parts[:-1]) if level > 1 else None
    else:
        level = 1
        parent_id = None
    
    full_path = f"{section_id} {title}".strip()
    
    # Initialize tags array
    tags = []
    
    # Add figure/table tags if applicable
    if FIGURE_TABLE_PATTERN.search(title):
        tags.append("figure" if "Figure" in title else "table")
    
    return {
        "doc_title": doc_title,
        "section_id": section_id,
        "title": title,
        "page": page,
        "level": level,
        "parent_id": parent_id,
        "full_path": full_path,
        "tags": tags
    }

def _extract_section_content(
    text_pages: List[str], 
    section: Dict[str, Any], 
    next_section: Optional[Dict[str, Any]]
) -> str:
    """Helper function to extract content for a specific section."""
    start_page = section["page"] - 1
    end_page = next_section["page"] - 1 if next_section else len(text_pages)
    
    # Ensure page indices are valid
    start_page = max(0, min(start_page, len(text_pages) - 1))
    end_page = min(end_page, len(text_pages))
    
    content_parts = []
    
    # Process start page (find section heading)
    page_text = text_pages[start_page]
    header_pattern = re.escape(section["section_id"])
    header_match = re.search(header_pattern, page_text, re.IGNORECASE)
    
    if header_match:
        start_pos = header_match.end()
        content_parts.append(page_text[start_pos:].strip())
    else:
        content_parts.append(page_text.strip())
    
    # Process middle pages
    for page_num in range(start_page + 1, end_page):
        content_parts.append(text_pages[page_num].strip())
    
    # Process end page (stop before next section heading)
    if next_section and end_page < len(text_pages):
        end_page_text = text_pages[end_page]
        next_header_pattern = re.escape(next_section["section_id"])
        next_header_match = re.search(next_header_pattern, end_page_text, re.IGNORECASE)
        
        if next_header_match:
            end_pos = next_header_match.start()
            content_parts.append(end_page_text[:end_pos].strip())
        else:
            content_parts.append(end_page_text.strip())
    
    return " ".join(content_parts).strip()

def parse_document_sections(
    text_pages: List[str], 
    toc_entries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Extract content for all sections based on TOC information."""
    print("📑 Parsing document sections...")
    parsed_sections = []
    
    # Sort TOC entries by page number for sequential processing
    sorted_toc = sorted(toc_entries, key=lambda x: x["page"])
    
    for i, section in enumerate(sorted_toc):
        next_section = sorted_toc[i + 1] if i + 1 < len(sorted_toc) else None
        content = _extract_section_content(text_pages, section, next_section)
        
        section_with_content = section.copy()
        section_with_content["content"] = content
        parsed_sections.append(section_with_content)
    
    print(f"Parsed content for {len(parsed_sections)} sections.")
    return parsed_sections

def generate_validation_report(
    toc_entries: List[Dict[str, Any]], 
    parsed_sections: List[Dict[str, Any]]
) -> None:
    """Generate a detailed validation report comparing TOC and parsed sections."""
    print("📊 Generating validation report...")
    
    # Handle empty TOC scenario
    if not toc_entries:
        print("⚠️ No Table of Contents entries found. Creating empty validation report.")
        report_path = os.path.join(OUTPUT_DIR, "validation_report_fixed.xlsx")
        
        # Create empty report
        with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
            pd.DataFrame([["No TOC entries found"]], columns=["Status"]).to_excel(
                writer, sheet_name="Summary", index=False
            )
            pd.DataFrame([], columns=["section_id", "title", "page"]).to_excel(
                writer, sheet_name="Detailed Comparison", index=False
            )
        
        print(f"✅ Empty validation report saved to {report_path}")
        return
    
    # Create DataFrames for comparison
    toc_df = pd.DataFrame(toc_entries)[["section_id", "title", "page"]]
    parsed_df = pd.DataFrame(parsed_sections)[["section_id", "title", "page"]]
    
    # Merge for comparison
    comparison_df = pd.merge(
        toc_df, 
        parsed_df, 
        on="section_id", 
        how="outer", 
        suffixes=("_toc", "_parsed")
    )
    
    # Identify mismatches
    toc_only = comparison_df[comparison_df["title_parsed"].isna()]
    parsed_only = comparison_df[comparison_df["title_toc"].isna()]
    
    # Create report data
    report_data = [
        ["Metric", "Value"],
        ["Total Sections in TOC", len(toc_entries)],
        ["Total Sections Parsed", len(parsed_sections)],
        ["Sections Matched", len(comparison_df.dropna())],
        ["Sections in TOC only", len(toc_only)],
        ["Sections in Parsed only", len(parsed_only)]
    ]
    
    # Add detailed mismatch information
    if not toc_only.empty:
        report_data.append(["Sections in TOC only:", ""])
        for _, row in toc_only.iterrows():
            report_data.append([
                f"{row['section_id']} - {row['title_toc']}", ""
            ])
    
    if not parsed_only.empty:
        report_data.append(["Sections in Parsed only:", ""])
        for _, row in parsed_only.iterrows():
            report_data.append([
                f"{row['section_id']} - {row['title_parsed']}", ""
            ])
    
    # Save to Excel
    report_path = os.path.join(OUTPUT_DIR, "validation_report_fixed.xlsx")
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        pd.DataFrame(report_data[1:], columns=report_data[0]).to_excel(
            writer, sheet_name="Summary", index=False
        )
        comparison_df.to_excel(
            writer, sheet_name="Detailed Comparison", index=False
        )
    
    print(f"✅ Validation report saved to {report_path}")

def save_jsonl(data: List[Dict[str, Any]], filename: str) -> None:
    """Save data to a JSONL file in the output directory."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    print(f"✅ Saved {filename}")

def main() -> None:
    """Main execution flow to orchestrate the PDF parsing process."""
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory '{OUTPUT_DIR}' created.")
    
    try:
        # Extract text from PDF
        text_pages = extract_text_from_pdf(PDF_PATH)
        
        # Set document title from PDF
        doc_title = "Universal Serial Bus Power Delivery Specification, Revision 3.2, Version 1.1, 2024-10"
        
        # Find and parse TOC content
        toc_lines = find_toc_content(text_pages)
        toc_entries = parse_toc_entries(toc_lines, doc_title)
        
        # Parse document sections
        parsed_sections = parse_document_sections(text_pages, toc_entries)
        
        # Save outputs
        save_jsonl(toc_entries, "usb_pd_toc_fixed.jsonl")
        save_jsonl(parsed_sections, "usb_pd_spec_fixed.jsonl")
        
        # Generate validation report
        generate_validation_report(toc_entries, parsed_sections)
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()