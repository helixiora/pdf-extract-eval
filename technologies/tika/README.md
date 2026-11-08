# Apache Tika PDF Extraction

This implementation uses Apache Tika 4.2.0 with OCR capabilities for PDF text extraction.

## Features

- Text extraction from both text-based and scanned PDFs
- OCR support using Tesseract (Dutch + English)
- JPEG2000 image support
- Multiple output formats:
  - HTML output (primary format)
  - Plain text
  - Basic Markdown (converted from HTML)
- Metadata extraction
- Configurable OCR settings

## Technical Details

### Docker Configuration
- Base image: `apache/tika:4.2.0-1-full`
- Custom configuration for OCR and JPEG2000 support
- Memory allocation: 6GB container limit; Tika 4 manages its parser worker heap
- Health checks enabled

### OCR Configuration
- Languages: Dutch (nld) and English (eng)
- Image processing:
  - DPI: 300
  - Format: PNG
  - Quality: 0.85
- Configurable size limits for OCR processing

### Output Processing
- Primary HTML output
- HTML to Markdown conversion using html2text
- Limited formatting preservation in Markdown
- Basic table conversion
- Unicode character support
- Link preservation

## Usage

1. Start the Tika server:
```bash
docker compose up -d
```

2. Process PDF files:
```bash
python parse_pdf.py
```

The script will:
1. Process all PDFs from the `../../documents/` directory
2. Generate output files in `../../results/tika/`:
   - `{filename}.md` - Markdown version
   - `{filename}.html` - HTML version
   - `{filename}_text.txt` - Plain text version
   - `{filename}_metadata.json` - Extracted metadata

## Configuration

### OCR Settings
Edit `tika-config.json` to modify:
- OCR language support
- Image processing parameters
- File size limits
- Parser timeouts

### Docker Resources
Edit `docker-compose.yml` to adjust:
- Memory allocation
- Port mapping
- Volume mounts
- Server command and read-only configuration mount

## Limitations

- OCR processing can be memory-intensive
- Large PDFs may require increased timeout settings
- Some complex PDF layouts may not preserve formatting perfectly
- This client converts HTML to Markdown; conversion loses some formatting
- Table structures often break in Markdown conversion
- Complex formatting (columns, footnotes) may be lost in Markdown

## Evaluation Results

### 1. Cost and Scalability
- ✅ Free, open-source solution
- ✅ Self-hosted with no per-document costs
- ⚠️ Resource intensive for OCR (size the container for the document workload)
- ⚠️ Processing speed varies significantly with OCR enabled

### 2. Accuracy and Quality
- ✅ Excellent for text-based PDFs
- ✅ Good OCR quality with Tesseract
- ✅ Multi-language support (configurable)
- ⚠️ Table structure preservation needs improvement

### 3. Output Formats
- ⚠️ This client uses HTML conversion for Markdown
- ⚠️ Markdown conversion loses complex formatting
- ✅ Clean HTML output
- ✅ Rich metadata extraction
- ⚠️ Table formatting often breaks in Markdown
- ⚠️ Limited control over Markdown output quality

### 4. Real-world Performance
- ✅ Handles complex layouts well in HTML
- ✅ Good image extraction
- ⚠️ Form field detection is basic
- ⚠️ May struggle with heavily formatted documents
- ⚠️ Markdown conversion reduces formatting quality

### 5. Production Readiness
- ✅ Official Docker container available
- ✅ REST API built-in
- ✅ Extensive documentation
- ✅ Health checks and monitoring
- ✅ Production-grade error handling

### 6. Project Activity
- ✅ Very active development (Apache Foundation)
- ✅ Regular releases
- ✅ Large community
- ✅ Quick security patch responses

### 7. Licensing
- ✅ Apache License 2.0
- ✅ Permissive for commercial use
- ✅ No royalty requirements
- ✅ Clear patent provisions

### 8. Privacy and Security
- ✅ Fully on-premises deployment
- ✅ No data leaves your infrastructure
- ✅ No data retention
- ✅ Regular security updates

## Tika 4 compatibility and local validation

Tika 4 loads `tika-config.json` via the explicit `-c` server argument. The
configuration preserves OCR-only processing, 300 DPI RGB PNG rendering and
Dutch + English recognition. The image installs the Dutch Tesseract model.
The client requests `/tika/html`; Tika 4 no longer selects HTML through
`Accept` or accepts the former `X-Tika-PDF*` configuration headers. OCR
response headers are no longer available, so metadata reports that the
server does not supply an OCR-applied flag.

The Compose port is bound to loopback. Tests may also target an independently
started loopback container without invoking Compose or processing repository
documents. From this directory, run:

```bash
python -m pip install -r requirements.txt -r requirements-test.txt
python -m unittest discover -s tests -v
# Optional: point only at a disposable local Tika 4.2.0 service.
TIKA_TEST_URL=http://127.0.0.1:9998 python -m unittest discover -s tests -v
```

The optional integration tests create their own text and scanned PDFs in
temporary directories, verify real OCR, HTML, Markdown and PDF metadata, and
never start containers or read existing documents. Without `TIKA_TEST_URL`,
only the five client regression tests run.

Migration references: [Tika Server 4 migration](https://tika.apache.org/docs/4.2.x/migration-to-4x/migrating-tika-server-4x.html),
[PDF configuration](https://tika.apache.org/docs/4.2.x/configuration/parsers/pdf-parser.html),
and [Tesseract configuration](https://tika.apache.org/docs/4.2.x/configuration/parsers/tesseract-ocr-parser.html).

The server enforces a 300-second whole-document budget, including embedded
documents, with a 120-second progress watchdog. Client parsing reads allow
450 seconds: the document budget plus watchdog wind-down and 30 seconds of
response slack. Readiness timeouts are retried within the bounded polling loop.
See [Tika timeout behavior](https://tika.apache.org/docs/4.2.x/pipes/timeouts.html).
