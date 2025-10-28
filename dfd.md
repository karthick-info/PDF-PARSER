# Data Flow Diagram (DFD)

```mermaid
flowchart TD

    %% Input
    PDFFile["📄 PDF File<br>(USB_PD_R3_2.pdf)"]

    %% Text Extraction
    Extractor["🧾 Text Extraction Module<br>extract_text_from_pdf()"]
    TOCFinder["📑 TOC Finder<br>find_toc_content()"]
    TOCParser["⚙️ TOC Parser<br>parse_toc_entries()"]

    %% Section Processing
    SectionParser["📘 Section Parser<br>parse_document_sections()"]

    %% Data Saving
    DataSaver["💾 Data Saver<br>save_jsonl()"]
    Metadata["🧠 Metadata Generator<br>generate_metadata_file()"]
    Validator["📊 Validation Report<br>generate_validation_report()"]

    %% Storage
    TOCFile[(usb_pd_toc.jsonl)]
    SpecFile[(usb_pd_spec.jsonl)]
    MetaFile[(usb_pd_metadata.jsonl)]
    ReportFile[(validation_report.xlsx)]
    LogFile[(process.log)]

    %% Users
    Developer["👨‍💻 Developer / Analyst"]
    System["🖥️ System Console"]

    %% Flow Connections
    PDFFile -->|Input PDF| Extractor
    Extractor -->|Extracts text pages| TOCFinder
    TOCFinder -->|Finds TOC lines| TOCParser
    TOCParser -->|Creates structured TOC| SectionParser
    SectionParser -->|Extracts section content| DataSaver
    DataSaver -->|Saves structured data| TOCFile
    DataSaver -->|Saves extracted content| SpecFile
    SectionParser --> Metadata
    Metadata -->|Stores document info| MetaFile
    SectionParser --> Validator
    Validator -->|Generates comparison report| ReportFile
    Extractor -->|Logs progress| LogFile
    TOCFinder -->|Logs errors & steps| LogFile
    Validator -->|Logs completion| LogFile
    LogFile --> Developer
    ReportFile --> Developer
    TOCFile --> Developer
    SpecFile --> Developer
