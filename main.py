# -*- coding: utf-8 -*-
"""
USB Power Delivery (USB PD) Specification Parsing and Structuring System.

Enhanced with structured logging for traceability, performance, and reliability.

Logging Features:
-----------------
1. Logs inputs/outputs of key functions.
2. Tracks data sizes, memory usage, and execution times.
3. Captures exceptions, errors, and unusual behavior.
4. Produces rotating log files with timestamps.
"""

import json
import os
import re
import time
import psutil
import logging
import tracemalloc
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
import pandas as pd

# ---------------- CONFIGURATION ----------------
PDF_PATH = "USB_PD_R3_2 V1.1 2024-10.pdf"
OUTPUT_DIR = "output_fixed"
LOG_FILE = os.path.join(OUTPUT_DIR, "usb_pd_parser.log")

# ---------------- LOGGER SETUP ----------------
def setup_logger():
    """Set up structured logger with file and console handlers."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger = logging.getLogger("USB_PD_Parser")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console handler (for essential updates)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()

# Precompiled regex patterns for efficiency
TOC_ENTRY_PATTERN = re.compile(
    r"^(?P<section_id>(\d+(\.\d+)*)|([A-Za-z][\w\s]*))\s+"
    r"(?P<title>[^\.]{3,})\s+"
    r"(?P<page>\d+)\s*$"
)
FIGURE_TABLE_PATTERN = re.compile(r"\b(Figure|Table)\s+\d+", re.IGNORECASE)


# ---------------- UTILITY FUNCTIONS ----------------
def log_performance(func):
    """Decorator to log execution time, memory usage, and input/output details."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        tracemalloc.start()
        process = psutil.Process(os.getpid())

        logger.debug(f"START {func.__name__} | args={len(args)}, kwargs={list(kwargs.keys())}")

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            mem_current, mem_peak = tracemalloc.get_traced_memory()
            cpu_percent = process.cpu_percent(interval=None)

            if isinstance(result, (list, dict)):
                size_info = f"output_size={len(result)}"
            else:
                size_info = "output_size=N/A"

            logger.info(
                f"{func.__name__} completed | time={elapsed:.3f}s | "
                f"mem_used={mem_current/1024:.1f}KB | peak_mem={mem_peak/1024:.1f}KB | "
                f"cpu={cpu_percent}% | {size_info}"
            )
            tracemalloc.stop()
            return result
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            tracemalloc.stop()
            raise
    return wrapper


# ---------------- CORE FUNCTIONS ----------------
@log_performance
def extract_text_from_pdf(pdf_path: str) -> List[str]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    with fitz.open(pdf_path) as doc:
        pages = [page.get_text("text") for page in doc]
        logger.debug(f"Extracted {len(pages)} pages from PDF.")
        return pages


@log_performance
def find_toc_content(text_pages: List[str]) -> List[str]:
    toc_lines = []
    for i, text in enumerate(text_pages):
        for line in text.split('\n'):
            if TOC_ENTRY_PATTERN.match(line.strip()):
                toc_lines.append((i, line.strip()))

    if not toc_lines:
        raise RuntimeError("Could not find Table of Contents content.")
    
    logger.debug(f"Found {len(toc_lines)} TOC lines across pages.")
    return toc_lines


@log_performance
def parse_toc_entries(toc_lines: List[Tuple[int, str]], doc_title: str) -> List[Dict[str, Any]]:
    toc_entries = []
    for page_num, line in toc_lines:
        entry = parse_toc_entry(line, doc_title)
        if entry:
            entry['page'] = page_num + 1
            toc_entries.append(entry)
    logger.debug(f"TOC entries parsed: {len(toc_entries)}")
    return toc_entries


def parse_toc_entry(line: str, doc_title: str) -> Optional[Dict[str, Any]]:
    match = TOC_ENTRY_PATTERN.match(line.strip())
    if not match:
        return None
    section_id = match.group("section_id").strip()
    title = match.group("title").strip()
    page = int(match.group("page").strip())

    if re.match(r"^\d+(\.\d+)*$", section_id):
        parts = section_id.split(".")
        level = len(parts)
        parent_id = ".".join(parts[:-1]) if level > 1 else None
    else:
        level = 1
        parent_id = None

    tags = []
    if FIGURE_TABLE_PATTERN.search(title):
        tags.append("figure" if "Figure" in title else "table")

    return {
        "doc_title": doc_title,
        "section_id": section_id,
        "title": title,
        "page": page,
        "level": level,
        "parent_id": parent_id,
        "tags": tags,
    }


@log_performance
def parse_document_sections(text_pages: List[str], toc_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    parsed_sections = []
    sorted_toc = sorted(toc_entries, key=lambda x: x["page"])
    for i, section in enumerate(sorted_toc):
        next_section = sorted_toc[i + 1] if i + 1 < len(sorted_toc) else None
        content = _extract_section_content(text_pages, section, next_section)
        section_copy = section.copy()
        section_copy["content"] = content
        parsed_sections.append(section_copy)
    logger.debug(f"Document sections parsed: {len(parsed_sections)}")
    return parsed_sections


def _extract_section_content(text_pages, section, next_section) -> str:
    start_page = section["page"] - 1
    end_page = next_section["page"] - 1 if next_section else len(text_pages)
    content_parts = [text_pages[start_page].strip()]

    for page_num in range(start_page + 1, end_page):
        content_parts.append(text_pages[page_num].strip())

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


@log_performance
def generate_validation_report(toc_entries, parsed_sections):
    if not toc_entries:
        logger.warning("No TOC entries found. Generating empty report.")
        report_path = os.path.join(OUTPUT_DIR, "validation_report.xlsx")
        with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
            pd.DataFrame([["No TOC entries found"]], columns=["Status"]).to_excel(writer, sheet_name="Summary", index=False)
        logger.info(f"Empty validation report created: {report_path}")
        return

    toc_df = pd.DataFrame(toc_entries)[["section_id", "title", "page"]]
    parsed_df = pd.DataFrame(parsed_sections)[["section_id", "title", "page"]]
    comparison_df = pd.merge(toc_df, parsed_df, on="section_id", how="outer", suffixes=("_toc", "_parsed"))

    report_path = os.path.join(OUTPUT_DIR, "validation_report.xlsx")
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        comparison_df.to_excel(writer, sheet_name="Detailed Comparison", index=False)
    logger.info(f"Validation report saved: {report_path}")


@log_performance
def save_jsonl(data: List[Dict[str, Any]], filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    logger.debug(f"Saved {filename} with {len(data)} records.")


@log_performance
def generate_metadata_file(toc_entries):
    if not toc_entries:
        logger.warning("Cannot generate metadata file — TOC entries missing.")
        return

    first_entry = toc_entries[0]
    metadata = {
        "doc_title": first_entry.get("doc_title", "Unknown Document"),
        "date_processed": datetime.now().isoformat(),
        "total_sections": len(toc_entries),
        "source_file": PDF_PATH,
        "processing_script_version": "1.0.0",
    }
    save_jsonl([metadata], "usb_pd_metadata.jsonl")
    logger.info("Metadata file generated.")


# ---------------- MAIN EXECUTION ----------------
@log_performance
def main():
    logger.info("=== USB Power Delivery Parser Started ===")
    try:
        text_pages = extract_text_from_pdf(PDF_PATH)
        doc_title = "Universal Serial Bus Power Delivery Specification, Revision 3.2, Version 1.1, 2024-10"

        toc_lines = find_toc_content(text_pages)
        toc_entries = parse_toc_entries(toc_lines, doc_title)
        parsed_sections = parse_document_sections(text_pages, toc_entries)

        save_jsonl(toc_entries, "usb_pd_toc.jsonl")
        save_jsonl(parsed_sections, "usb_pd_spec.jsonl")
        generate_metadata_file(toc_entries)
        generate_validation_report(toc_entries, parsed_sections)

        logger.info("=== USB Power Delivery Parser Completed Successfully ===")

    except Exception as e:
        logger.exception(f"Critical failure during processing: {e}")
        raise


if __name__ == "__main__":
    main()
