# System Architecture Diagram

```mermaid
graph TD

    %% Input
    subgraph Input
        PDFFile["📄 PDF Document
        Example: USB_PD_R3_2.pdf
        Input: Unstructured text & pages
        Output: Sent for processing"]
    end

    %% Processing Components
    subgraph Processing
        Extractor["🧾 extract_text_from_pdf()
        Input: PDF file path
        Task: Read all pages & extract text
        Output: List of text pages"]

        TOCFinder["📑 find_toc_content()
        Input: Extracted text pages
        Task: Locate Table of Contents (TOC)
        Output: TOC lines"]

        TOCParser["⚙️ parse_toc_entries()
        Input: TOC lines + Document title
        Task: Structure TOC (section_id, title, page)
        Output: List of TOC entries"]

        SectionParser["📘 parse_document_sections()
        Input: Text pages + TOC entries
        Task: Extract each section’s text
        Output: Section-wise structured content"]

        DataSaver["💾 save_jsonl()
        Input: TOC entries + Section content
        Task: Save as JSONL data files
        Output: usb_pd_toc.jsonl & usb_pd_spec.jsonl"]

        MetadataGen["🧠 generate_metadata_file()
        Input: TOC entries
        Task: Create summary info (title, date, sections)
        Output: usb_pd_metadata.jsonl"]

        Validator["📊 generate_validation_report()
        Input: TOC entries + Parsed sections
        Task: Compare TOC vs Extracted data
        Output: validation_report.xlsx"]

        Logger["📝 Logger
        Input: Process steps, errors, performance
        Task: Track progress, execution time & issues
        Output: process.log"]
    end

    %% Storage
    subgraph OutputStorage
        TOCFile["📂 usb_pd_toc.jsonl
        Contains: Structured TOC data"]

        SpecFile["📂 usb_pd_spec.jsonl
        Contains: Section-wise extracted content"]

        MetaFile["📂 usb_pd_metadata.jsonl
        Contains: Document summary info"]

        ReportFile["📊 validation_report.xlsx
        Contains: Comparison report (TOC vs Parsed)"]

        LogFile["📄 process.log
        Contains: Logs of execution & performance"]
    end

    %% Flow Connections
    PDFFile --> Extractor
    Extractor --> TOCFinder
    TOCFinder --> TOCParser
    TOCParser --> SectionParser
    SectionParser --> DataSaver
    DataSaver --> MetadataGen
    MetadataGen --> Validator
    Validator -->|Save results| OutputStorage
    Logger --> LogFile
