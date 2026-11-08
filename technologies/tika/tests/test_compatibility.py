"""Offline client tests; optional loopback integration uses only synthetic PDFs."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("parse_pdf", ROOT / "parse_pdf.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClientCompatibility(unittest.TestCase):
    def test_html_handler_and_no_obsolete_ocr_header(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "synthetic.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%%EOF")
            client = module.TikaServer()
            client.is_ready = True
            metadata = Mock(status_code=200)
            metadata.json.return_value = {"Content-Type": "application/pdf"}
            html = Mock(status_code=200, text="<html><body><p>Synthetic content</p></body></html>")
            with patch.object(module.requests, "put", side_effect=[metadata, html]) as put:
                content, result, raw_html = client.parse_pdf(str(pdf))
            self.assertIn("Synthetic content", content)
            self.assertIn("<html>", raw_html)
            self.assertEqual(put.call_args_list[1].args[0], "http://localhost:9998/tika/html")
            self.assertNotIn("X-Tika-PDFOcrStrategy", put.call_args_list[1].kwargs.get("headers", {}))
            self.assertEqual(result["OCR-Applied"], "Not reported by Tika 4")

    def test_metadata_parse_exception_is_not_silent_success(self):
        with tempfile.NamedTemporaryFile() as pdf:
            client = module.TikaServer()
            client.is_ready = True
            response = Mock(status_code=200)
            response.json.return_value = {"tk:exception:container-exception": "synthetic parse error"}
            with patch.object(module.requests, "put", return_value=response):
                self.assertIn("error", client.extract_metadata(pdf.name))


@unittest.skipUnless(os.environ.get("TIKA_TEST_URL"), "set TIKA_TEST_URL to an isolated loopback Tika 4 service")
class SyntheticIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ["TIKA_TEST_URL"]
        if urlparse(url).hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Integration tests require a loopback service")
        cls.client = module.TikaServer(url)
        # Test infrastructure starts its own container; never invoke Docker Compose.
        cls.client.is_ready = True
        response = module.requests.get(url.rstrip("/") + "/version", timeout=10)
        response.raise_for_status()
        assert "4.2.0" in response.text, response.text

    def test_text_pdf_to_html_and_markdown(self):
        from reportlab.pdfgen.canvas import Canvas
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-text.pdf"
            canvas = Canvas(str(path))
            canvas.setFont("Helvetica", 24)
            canvas.drawString(60, 700, "Synthetic HELIXIORA fixture")
            canvas.save()
            content, metadata, html = self.client.parse_pdf(str(path))
            self.assertIsNotNone(html, content)
            self.assertIn("<html", html.lower())
            self.assertIn("HELIXIORA", content)
            self.assertNotIn("error", metadata)
            self.assertEqual(metadata.get("Content-Type"), "application/pdf")

    def test_scanned_pdf_requires_real_ocr(self):
        from PIL import Image, ImageDraw, ImageFont
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-scan.pdf"
            image = Image.new("RGB", (1800, 1000), "white")
            font = ImageFont.load_default(size=70)
            ImageDraw.Draw(image).text((100, 300), "HELIXIORA SCANNED FIXTURE", fill="black", font=font)
            image.save(path, "PDF", resolution=150)
            content, metadata, html = self.client.parse_pdf(str(path))
            self.assertIsNotNone(html, content)
            self.assertIn("HELIXIORA", content)
            self.assertIn("SCANNED", content)
            self.assertNotIn("error", metadata)


if __name__ == "__main__":
    unittest.main()
