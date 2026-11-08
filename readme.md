# PDF Extraction Technology Testbed

This repository serves as a testing ground for various PDF text extraction technologies. It provides a structured environment to evaluate and compare different PDF extraction tools and libraries.

## Currently Implemented Technologies

### 1. Apache Tika (with OCR)

Located in `technologies/tika/`

- Uses Apache Tika 4.2.0 with Tesseract OCR
- Supports both text-based and scanned PDFs
- Includes JPEG2000 image support
- Primary HTML output with conversion to other formats
- ⚠️ No native Markdown support (HTML conversion required)

## Planned Technologies

### Commercial Cloud Services

#### 1. OpenAI PDF Understanding
- Part of GPT-4 Vision API
- Pros: High accuracy, native markdown output, good at complex layouts
- Cons: Cloud-based, potential privacy concerns, cost per page
- Status: Released in March 2024

#### 2. Google Document AI
- Enterprise-grade document processing
- Pros: High accuracy, form field detection, table extraction
- Cons: Cloud-based, enterprise pricing, complex setup
- Status: Generally available

#### 3. Microsoft Azure Form Recognizer
- Part of Azure Cognitive Services
- Pros: Good form detection, pre-built models, custom training
- Cons: Cloud-based, requires Azure subscription
- Status: Generally available

### Open Source Solutions

#### 4. Unstructured
- Python-based document processing library
- Pros: Native markdown support, active development, good table handling
- Cons: Still maturing, resource intensive
- Status: Active development, regular releases

#### 5. PyMuPDF (fitz)
- Python bindings for MuPDF
- Pros: Fast, lightweight, good for text-based PDFs
- Cons: Limited OCR capabilities, basic layout analysis
- Status: Stable, actively maintained

#### 6. Other Candidates
- PDFPlumber: Good for table extraction
- PdfMiner.six: Pure Python, good for text extraction
- Camelot: Specialized in table extraction
- Nougat: Scientific paper extraction (by Meta)
- Adobe PDF Services API: Commercial offering with good accuracy

## Evaluation Criteria

Each PDF extraction technology is evaluated based on the following criteria:

### 1. Cost and Scalability
- Cost per individual PDF processing
- Pricing for bulk processing (thousands of PDFs)
- Resource requirements (CPU, memory, storage)
- Processing speed and throughput capabilities

### 2. Accuracy and Quality
- Text extraction accuracy (compared to original)
- OCR quality for scanned documents
- Handling of different languages and character sets
- Preservation of document structure and formatting

### 3. Output Formats
- Markdown output capability for LLM/vector database integration
- Quality of markdown conversion
- Support for other formats (HTML, plain text, JSON)
- Metadata extraction capabilities

### 4. Real-world Performance
- Handling of complex layouts (columns, tables, footnotes)
- Image and diagram extraction
- Form field recognition
- Error handling and recovery
- Performance with corrupted or malformed PDFs

### 5. Production Readiness
- Docker container availability
- REST API support
- Documentation quality
- Monitoring and logging capabilities
- Error reporting and handling
- Scalability features

### 6. Project Activity
- Development activity (commits, releases)
- Community size and engagement
- Issue resolution time
- Long-term maintenance outlook

### 7. Licensing
- Open source availability
- License type and restrictions
- Commercial use terms
- Patent claims and protections

### 8. Privacy and Security
- Data handling practices
- Cloud vs on-premises deployment
- Data retention policies
- Security features and certifications

## Repository Structure

```tree
.
├── documents/              # Test documents
│   ├── scanned/           # Scanned PDF documents
│   ├── text-based/        # Text-based PDF documents
│   └── mixed/             # PDFs with both text and scanned content
├── technologies/          # Different extraction technologies
│   └── tika/             # Apache Tika implementation
└── results/              # Extraction results for comparison
    └── tika/             # Tika extraction results
```

## Getting Started

### Prerequisites

- Docker
- Python 3.x
- pip (Python package manager)

### Running Tests with Apache Tika

1. Navigate to the Tika implementation:

```bash
cd technologies/tika
```

2. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

3. Start the Tika service:

```bash
docker compose up -d
```

4. Process PDF files:

```bash
python parse_pdf.py
```

## Adding New Technologies

To add a new PDF extraction technology:

1. Create a new directory under `technologies/`
2. Include all necessary implementation files
3. Provide a README with setup and usage instructions
4. Ensure the implementation can process files from the `documents/` directory
5. Output results to the corresponding directory under `results/`

## Contributing

When adding a new technology or test document:

1. Place test documents in the appropriate `documents/` subdirectory
2. Create a new technology directory with a descriptive name
3. Include clear setup instructions
4. Document any special requirements or limitations
5. Add the technology to the list in this README

## License

[Add your license information here]
