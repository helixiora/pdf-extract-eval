import os
import requests
import subprocess
import time
import glob
import re
import json
from typing import Dict, Any, Tuple, Optional
import html2text

# Server budget: 300s document deadline + 120s watchdog grace + 30s response slack.
PARSE_REQUEST_TIMEOUT = (5, 450)


class TikaServer:
    """Manages Tika server connection and status."""

    def __init__(self, base_url: str = "http://localhost:9998"):
        self.base_url = base_url.rstrip("/")
        self.is_ready = False
        self.version = None
        self.parsers = None

    def ensure_running(self) -> bool:
        """Ensure Tika container is running and ready."""
        if self.is_ready:
            return True

        # Check if container is running
        result = subprocess.run(
            ["docker", "compose", "ps", "-q", "tika"],
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print("Starting Tika container...")
            subprocess.run(["docker", "compose", "up", "-d"])
            time.sleep(3)

        # Wait for healthcheck to pass
        print("Waiting for Tika service to be ready...")
        for _ in range(10):
            try:
                response = requests.get(f"{self.base_url}/tika", timeout=10)
                if response.status_code == 200:
                    print("Tika service is ready!")
                    self._check_version()
                    self.is_ready = True
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(1)

        print("Failed to start Tika service")
        return False

    def _check_version(self):
        """Check and store Tika version and capabilities."""
        try:
            response = requests.get(f"{self.base_url}/version", timeout=10)
            if response.status_code == 200:
                self.version = response.text
                print(f"Tika Server Version: {self.version}")

            parsers_response = requests.get(
                f"{self.base_url}/parsers/details",
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if parsers_response.status_code == 200:
                self.parsers = parsers_response.json()
                print("\nAvailable Parsers:")
                print(json.dumps(self.parsers, indent=2))
        except Exception as e:
            print(f"Warning: Error checking Tika version: {str(e)}")

    def extract_metadata(self, pdf_path: str) -> Dict[Any, Any]:
        """Extract metadata from PDF using Tika."""
        if not self.ensure_running():
            return {"error": "Tika server not available"}

        try:
            with open(pdf_path, "rb") as pdf_file:
                response = requests.put(
                    f"{self.base_url}/meta",
                    headers={"Accept": "application/json"},
                    data=pdf_file,
                    timeout=PARSE_REQUEST_TIMEOUT,
                )
                if response.status_code == 200:
                    metadata = response.json()
                    if "tk:exception:container-exception" in metadata:
                        metadata["error"] = "Tika reported a metadata parse exception"
                    return metadata
                return {"error": f"Failed to extract metadata: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error extracting metadata: {str(e)}"}

    def parse_pdf(
        self, pdf_path: str, output_format: str = "markdown"
    ) -> Tuple[Optional[str], Dict[Any, Any], Optional[str]]:
        """Parse PDF using Tika and return content, metadata, and HTML."""
        if not self.ensure_running():
            return None, {"error": "Tika server not available"}, None

        # Get absolute path of the PDF
        abs_path = os.path.abspath(pdf_path)
        content = None
        html_content = None
        error = None

        try:
            # First extract metadata
            metadata = self.extract_metadata(abs_path)

            # Read the PDF file
            with open(abs_path, "rb") as pdf_file:
                # Tika 4 selects the output handler in the URL. OCR is configured
                # on the server; the former X-Tika-PDF* headers are unsupported.
                response = requests.put(
                    f"{self.base_url}/tika/html",
                    data=pdf_file,
                    timeout=PARSE_REQUEST_TIMEOUT,
                )

                if response.status_code == 200:
                    html_content = response.text

                    # Tika 4 does not return the old OCR response headers. Do not
                    # mislabel successfully OCRed documents as non-OCR documents.
                    metadata["OCR-Applied"] = "Not reported by Tika 4"

                    if output_format == "markdown":
                        filename = os.path.basename(pdf_path)
                        title = os.path.splitext(filename)[0]
                        content = enhance_markdown(html_content, title)
                    elif output_format == "html":
                        content = html_content
                    else:  # plain text
                        converter = html2text.HTML2Text()
                        converter.ignore_links = True
                        converter.ignore_images = True
                        converter.ignore_emphasis = True
                        content = converter.handle(html_content)
                else:
                    error = (
                        f"Error parsing PDF: {response.status_code} - {response.text}"
                    )

        except Exception as e:
            error = f"Error processing {pdf_path}: {str(e)}"

        if error:
            return error, metadata, None

        return content, metadata, html_content


def enhance_markdown(html_content: str, title: str) -> str:
    """Convert HTML to Markdown with enhanced formatting."""
    # Configure html2text
    converter = html2text.HTML2Text()
    converter.body_width = 0  # Don't wrap lines
    converter.unicode_snob = True  # Use Unicode characters
    converter.protect_links = True  # Don't convert links to references
    converter.mark_code = True  # Use markdown code syntax
    converter.default_image_alt = "image"  # Default alt text for images

    # Convert HTML to markdown
    md_text = converter.handle(html_content)

    # Add title as H1
    md_text = f"# {title}\n\n{md_text}"

    # Post-process the markdown
    lines = md_text.split("\n")
    processed_lines = []
    in_table = False

    for line in lines:
        line = line.rstrip()

        # Skip multiple empty lines
        if not line and processed_lines and not processed_lines[-1]:
            continue

        # Improve table formatting
        if "|" in line and not line.startswith("http"):
            if not in_table:
                in_table = True
                if not any(c.isalpha() for c in line):  # If line contains only symbols
                    continue
            processed_lines.append(line)
            continue
        elif in_table:
            in_table = False
            processed_lines.append("")

        # Improve header formatting
        if line.isupper() and len(line) > 4:
            processed_lines.extend(["", f"## {line}", ""])
            continue

        processed_lines.append(line)

    return "\n".join(processed_lines)


def save_output(
    content: str,
    metadata: Dict[Any, Any],
    html_content: str,
    base_path: str,
    format: str,
) -> Tuple[str, str, str]:
    """Save the extracted content, metadata, and HTML to files."""
    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(base_path), exist_ok=True)

    # Save content
    content_ext = ".md" if format == "markdown" else ".txt"
    content_path = f"{base_path}{content_ext}"
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Save HTML
    html_path = f"{base_path}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Save metadata
    metadata_path = f"{base_path}_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return content_path, metadata_path, html_path


def main():
    # Initialize Tika server
    tika = TikaServer()
    if not tika.ensure_running():
        print("Error: Could not start Tika server")
        return

    # Define document directories to process
    doc_dirs = [
        "../../documents/scanned",
        "../../documents/text-based",
        "../../documents/mixed",
    ]

    # Get all PDF files from document directories
    pdf_files = []
    for doc_dir in doc_dirs:
        if os.path.exists(doc_dir):
            pdf_files.extend(glob.glob(f"{doc_dir}/*.pdf"))

    if not pdf_files:
        print("No PDF files found in the documents directories!")
        return

    print(f"Found {len(pdf_files)} PDF files to process.")
    print("=" * 80)

    for pdf_file in sorted(pdf_files):
        print(f"\nProcessing: {pdf_file}")
        print("-" * 80)

        # Extract content and metadata
        content, metadata, html_content = tika.parse_pdf(
            pdf_file, output_format="markdown"
        )

        if isinstance(content, str) and content.startswith("Error"):
            print(f"Error processing {pdf_file}: {content}")
            continue

        # Create output path in results directory
        rel_path = os.path.relpath(pdf_file, "../../documents")
        doc_type = os.path.dirname(rel_path)  # scanned, text-based, or mixed
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        output_base = f"../../results/tika/{doc_type}/{base_name}"

        # Save content, metadata, and HTML
        content_path, metadata_path, html_path = save_output(
            content, metadata, html_content, output_base, "markdown"
        )

        # Print preview and metadata summary
        preview_lines = content.split("\n")[:10]
        print("Preview of markdown:")
        print("\n".join(preview_lines))
        print(f"\nContent saved to: {content_path}")
        print(f"HTML saved to: {html_path}")
        print(f"Metadata saved to: {metadata_path}")

        # Print interesting metadata if available
        interesting_fields = [
            "Author",
            "Creation-Date",
            "Page-Count",
            "Content-Type",
            "OCR-Applied",
            "OCR-Language",
        ]
        print("\nKey metadata:")
        for field in interesting_fields:
            if field in metadata:
                print(f"{field}: {metadata[field]}")

        print("-" * 80)


if __name__ == "__main__":
    main()
