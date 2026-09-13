from __future__ import annotations

import importlib.util
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CRAWL_SCRIPTS = ROOT / "skills" / "crawl-render-audit" / "scripts"
if str(CRAWL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CRAWL_SCRIPTS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


safe_url = load("aura_safe_url_test", CRAWL_SCRIPTS / "safe_url.py")
crawl = load("aura_live_crawl_test", CRAWL_SCRIPTS / "crawl.py")


class LiveProtocolTests(unittest.TestCase):
    def test_rejects_nonpublic_and_nonhttp_targets(self):
        for target in ("http://localhost", "http://127.0.0.1", "http://169.254.169.254", "file:///tmp/site"):
            with self.assertRaises(ValueError, msg=target):
                safe_url.validate_public_url(target)

    @patch("aura_safe_url_test.socket.getaddrinfo")
    def test_accepts_resolved_public_target(self, resolver):
        resolver.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]
        self.assertEqual("https://example.com/", safe_url.validate_public_url("https://example.com"))

    def test_crawl_writes_one_deterministic_html_artifact_set(self):
        cache = ROOT / "work" / "live-protocol-test-cache"
        result = crawl.crawl(str(ROOT / "fixtures" / "healthy-ssg"), crawl.CrawlConfig(max_pages=10, delay=0), cache)
        artifacts = sorted(cache.glob("*.html"))
        self.assertEqual(len(result["pages"]), len(artifacts))
        self.assertTrue(all("artifact_path" in page for page in result["pages"]))
        self.assertTrue(all(path.read_text(encoding="utf-8") for path in artifacts))


if __name__ == "__main__":
    unittest.main()
