from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "crawl-render-audit" / "scripts"
FIXTURES = ROOT / "fixtures"

def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module

crawl = load("crawl")
render_diff = load("render_diff")
structured_data = load("structured_data")

class CrawlLayerTests(unittest.TestCase):
    def fixture(self, name: str) -> str:
        return (FIXTURES / name).resolve().as_uri()

    def test_healthy_static_crawls_and_sitemap_is_optional(self) -> None:
        result = crawl.crawl(self.fixture("healthy-ssg"), crawl.CrawlConfig(delay=0, max_pages=5))
        self.assertEqual(2, len(result["pages"]))
        self.assertTrue(result["robots_compliant"])
        self.assertFalse(result["truncated"])

    def test_robots_blocks_private_path_without_fetching(self) -> None:
        result = crawl.crawl(self.fixture("bot-blocked"), crawl.CrawlConfig(delay=0, max_pages=5))
        self.assertEqual(["file:///" + (FIXTURES / "bot-blocked" / "private.html").resolve().as_posix().lstrip("/")], result["blocked_by_robots"])
        self.assertEqual(1, len(result["pages"]))

    def test_real_render_gap_is_high_only_with_all_conditions(self) -> None:
        raw = (FIXTURES / "broken-spa" / "index.html").read_text(); rendered = (FIXTURES / "broken-spa" / "rendered.html").read_text()
        finding = render_diff.classify(raw, rendered, False, "/product/orbit")
        self.assertEqual("high", finding["severity"])
        self.assertIn("price", finding["missing_facts"])
        self.assertEqual("medium", render_diff.classify(raw, rendered, True)["severity"])

    def test_ssr_marker_prevents_high_render_gap(self) -> None:
        raw = "<script>window.__NUXT__={}</script><p>loading</p>"
        rendered = "<p>Price: $9.00</p>"
        self.assertEqual("informational", render_diff.classify(raw, rendered, False)["severity"])

    def test_invalid_product_schema_is_not_counted_valid(self) -> None:
        result = structured_data.analyse((FIXTURES / "shopify-like" / "index.html").read_text())
        self.assertEqual(1, result["present"]); self.assertEqual(0, result["valid"])
        self.assertEqual(["offers"], result["items"][0]["missing_required"])

    def test_microdata_service_is_valid(self) -> None:
        result = structured_data.analyse((FIXTURES / "docs-heavy" / "guide.html").read_text())
        self.assertEqual(1, result["valid"]); self.assertEqual(["Service"], result["types"])

    def test_cli_writes_deterministic_cache_and_json(self) -> None:
        cache_dir = ROOT / "work" / "test-cache"
        command = [sys.executable, str(SCRIPTS / "crawl.py"), self.fixture("empty"), "--delay", "0", "--cache-dir", str(cache_dir)]
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        output = json.loads(completed.stdout)
        self.assertTrue((cache_dir / "crawl.json").exists()); self.assertEqual(1, len(output["pages"]))

if __name__ == "__main__": unittest.main()
