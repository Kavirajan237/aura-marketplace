#!/usr/bin/env python3
"""Deterministic, read-only crawler for AURA. JSON is written only to stdout."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0, str(SCRIPT_DIR))
from safe_url import validate_public_url

EXIT_OK, EXIT_FINDINGS, EXIT_USAGE = 0, 1, 2


def log(message: str) -> None:
    print(message, file=sys.stderr)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.canonicals: list[str] = []
        self.noindex = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "a" and data.get("href"):
            self.links.append(data["href"] or "")
        if tag == "link" and (data.get("rel") or "").lower() == "canonical" and data.get("href"):
            self.canonicals.append(data["href"] or "")
        if tag == "meta" and (data.get("name") or "").lower() == "robots":
            self.noindex = "noindex" in (data.get("content") or "").lower()


@dataclass(frozen=True)
class Page:
    url: str
    status: int
    final_url: str
    redirected_from: list[str]
    html: str
    links: list[str]
    canonical: str | None
    noindex: bool


@dataclass(frozen=True)
class CrawlConfig:
    seed: int = 0
    max_pages: int = 30
    timeout: float = 10.0
    delay: float = 0.1
    max_concurrent: int = 2
    deadline_seconds: float | None = None


class RobotsRules:
    """Small deterministic robots parser: most-specific Allow/Disallow wins."""
    def __init__(self, text: str) -> None:
        self.rules: list[tuple[bool, str]] = []
        applies = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                applies = value in {"*", "AURA", "aura"}
            elif applies and key in {"allow", "disallow"} and value:
                self.rules.append((key == "allow", value))

    def allowed(self, path: str) -> bool:
        matches = [(len(rule), allow) for allow, rule in self.rules if path.startswith(rule)]
        return True if not matches else sorted(matches, key=lambda item: (item[0], item[1]))[-1][1]


def is_file_target(target: str) -> bool:
    return target.startswith("file://") or Path(target).exists()


def normalise_target(target: str) -> str:
    if Path(target).exists():
        return Path(target).resolve().as_uri()
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme not in {"http", "https", "file"}:
        raise ValueError("target must be http(s) URL or existing local file/directory")
    return target


def local_root(url: str) -> Path:
    path = Path(urllib.request.url2pathname(urllib.parse.urlparse(url).path))
    return path if path.is_dir() else path.parent


MAX_RESPONSE_BYTES = 2_000_000
MAX_REDIRECTS = 5

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def read_url(url: str, timeout: float) -> tuple[int, str, str, list[str], dict[str, str]]:
    """GET only. HTTPError remains a recorded status; no network write is possible."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "file":
        path = Path(urllib.request.url2pathname(parsed.path))
        if path.is_dir():
            path /= "index.html"
        if not path.exists():
            return 404, url, "", [], {}
        return 200, path.resolve().as_uri(), path.read_text(encoding="utf-8"), [], {}
    redirects: list[str] = []
    opener = urllib.request.build_opener(NoRedirect())
    current = validate_public_url(url)
    for _ in range(MAX_REDIRECTS + 1):
        request = urllib.request.Request(current, headers={"User-Agent": "AURA/1.0 (+read-only audit)"}, method="GET")
        try:
            with opener.open(request, timeout=timeout) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
                if len(payload) > MAX_RESPONSE_BYTES: raise ValueError("response exceeded 2 MB audit limit")
                return response.status, current, payload.decode(response.headers.get_content_charset() or "utf-8", "replace"), redirects, {k.lower(): v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            headers = {k.lower(): v for k, v in exc.headers.items()}
            if exc.code in {301, 302, 303, 307, 308} and headers.get("location"):
                redirects.append(current); current = validate_public_url(urllib.parse.urljoin(current, headers["location"])); continue
            return exc.code, current, "", redirects, headers
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            log(f"fetch failed {current}: {exc}")
            return 0, current, "", redirects, {}
    return 0, current, "", redirects, {}


def robots_for(start_url: str, timeout: float) -> tuple[RobotsRules, str | None]:
    parsed = urllib.parse.urlparse(start_url)
    if parsed.scheme == "file":
        candidate = local_root(start_url) / "robots.txt"
        return RobotsRules(candidate.read_text(encoding="utf-8") if candidate.exists() else ""), str(candidate) if candidate.exists() else None
    robots_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    status, _, body, _, _ = read_url(robots_url, timeout)
    return RobotsRules(body if status == 200 else ""), robots_url if status == 200 else None


def same_origin(start: str, candidate: str) -> bool:
    a, b = urllib.parse.urlparse(start), urllib.parse.urlparse(candidate)
    return (a.scheme, a.netloc) == (b.scheme, b.netloc) if a.scheme != "file" else b.scheme == "file" and str(local_root(start)) in urllib.request.url2pathname(b.path)


def page_url(start: str) -> str:
    parsed = urllib.parse.urlparse(start)
    if parsed.scheme == "file" and Path(urllib.request.url2pathname(parsed.path)).is_dir():
        return (Path(urllib.request.url2pathname(parsed.path)) / "index.html").resolve().as_uri()
    return start


def sitemap_urls(start: str, timeout: float) -> tuple[list[str], bool, bool]:
    parsed = urllib.parse.urlparse(start)
    if parsed.scheme == "file":
        source = local_root(start) / "sitemap.xml"
        if not source.exists(): return [], False, False
        text = source.read_text(encoding="utf-8")
    else:
        source = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/sitemap.xml", "", "", ""))
        status, _, text, _, _ = read_url(source, timeout)
        if status != 200: return [], False, False
    try:
        root = ET.fromstring(text)
        urls = sorted({node.text.strip() for node in root.iter() if node.tag.endswith("loc") and node.text})
        return urls, True, True
    except ET.ParseError:
        return [], False, True


def crawl(target: str, config: CrawlConfig, artifact_dir: Path | None = None) -> dict[str, object]:
    if config.max_pages < 1 or config.timeout <= 0 or config.delay < 0 or config.max_concurrent < 1:
        raise ValueError("max-pages, timeout, delay, and max-concurrent must be positive (delay may be zero)")
    begun = time.monotonic()
    start = normalise_target(target)
    if urllib.parse.urlparse(start).scheme in {"http", "https"}: start = validate_public_url(start)
    start = page_url(start)
    robots, robots_source = robots_for(start, config.timeout)
    sitemap, sitemap_parses, sitemap_present = sitemap_urls(start, config.timeout)
    sitemap = sorted({urllib.parse.urljoin(start, url) for url in sitemap})
    queue = sorted({start, *[u for u in sitemap if same_origin(start, u)]})
    visited: set[str] = set(); blocked: list[str] = []; pages: list[Page] = []
    deadline_hit = False
    while queue and len(pages) < config.max_pages:
        if config.deadline_seconds is not None and time.monotonic() - begun >= config.deadline_seconds:
            deadline_hit = True; break
        url = queue.pop(0)
        if url in visited: continue
        visited.add(url)
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or "/"
        if parsed.scheme == "file":
            # Robots paths are URL paths relative to the audited site root, not disk paths.
            try:
                path = "/" + Path(urllib.request.url2pathname(parsed.path)).resolve().relative_to(local_root(start).resolve()).as_posix()
            except ValueError:
                blocked.append(url); continue
        if not robots.allowed(path):
            blocked.append(url); continue
        status, final_url, html, redirects, headers = read_url(url, config.timeout)
        parser = LinkParser(); parser.feed(html)
        noindex = parser.noindex or "noindex" in headers.get("x-robots-tag", "").lower()
        links = sorted({urllib.parse.urldefrag(urllib.parse.urljoin(final_url, link))[0] for link in parser.links if urllib.parse.urljoin(final_url, link)})
        pages.append(Page(url, status, final_url, redirects, html, links, parser.canonicals[0] if parser.canonicals else None, noindex))
        for link in links:
            if same_origin(start, link) and link not in visited and link not in queue:
                queue.append(link)
        queue.sort()
        if queue and config.delay: time.sleep(config.delay)
    serial_pages = []
    if artifact_dir:
        artifact_dir.mkdir(parents=True, exist_ok=True)
    for page in sorted(pages, key=lambda p: p.url):
        item = asdict(page); item["content_sha256"] = hashlib.sha256(page.html.encode()).hexdigest(); del item["html"]
        if artifact_dir and page.status == 200 and page.html:
            filename = hashlib.sha256(page.url.encode()).hexdigest()[:16] + ".html"
            (artifact_dir / filename).write_text(page.html, encoding="utf-8")
            item["artifact_path"] = filename
        serial_pages.append(item)
    return {
        "site": urllib.parse.urlparse(start).netloc or local_root(start).name,
        "start_url": start, "config": asdict(config), "robots_source": robots_source,
        "robots_compliant": True, "blocked_by_robots": sorted(blocked), "sitemap": {"present": sitemap_present, "parses": sitemap_parses, "urls": sitemap},
        "pages": serial_pages, "pages_total_estimate": len(sitemap) if sitemap else len(serial_pages),
        "truncated": bool(queue) or deadline_hit, "deadline_hit": deadline_hit, "elapsed_ms": round((time.monotonic() - begun) * 1000)
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target"); parser.add_argument("--seed", type=int, default=0); parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=10.0); parser.add_argument("--delay", type=float, default=0.1); parser.add_argument("--max-concurrent", type=int, default=2)
    parser.add_argument("--cache-dir", type=Path, help="Optional local JSON cache directory")
    args = parser.parse_args(argv)
    try:
        result = crawl(args.target, CrawlConfig(args.seed, args.max_pages, args.timeout, args.delay, args.max_concurrent), args.cache_dir / "pages" if args.cache_dir else None)
    except (ValueError, OSError) as exc:
        log(f"usage error: {exc}"); return EXIT_USAGE
    if args.cache_dir:
        args.cache_dir.mkdir(parents=True, exist_ok=True)
        (args.cache_dir / "crawl.json").write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")
    json.dump(result, sys.stdout, sort_keys=True); sys.stdout.write("\n")
    return EXIT_OK


if __name__ == "__main__": raise SystemExit(main())
