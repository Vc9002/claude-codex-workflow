#!/usr/bin/env python3
"""Extract Handshake job links from a saved Handshake jobs HTML file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path


def normalize(value: str) -> str:
    value = value.replace("\u2014", "-").replace("\u2013", "-")
    value = re.sub(r"&amp;", "&", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip().casefold()


def similarity(needle: str, haystack: str) -> int:
    n = normalize(needle)
    h = normalize(haystack)
    if not n:
        return 0
    if n == h:
        return 100
    if n in h or h in n:
        return 80
    words = {w for w in re.split(r"[^a-z0-9]+", n) if w}
    target = {w for w in re.split(r"[^a-z0-9]+", h) if w}
    if not words:
        return 0
    return int(70 * len(words & target) / len(words))


def unescape_js_string(value: str) -> str:
    return json.loads(f'"{value}"')


def extract_initial_jobs(html: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    block_match = re.search(r"jobs:\s*\[(.*?)\]\s*[,}]", html, re.S)
    if not block_match:
        return jobs

    for obj_match in re.finditer(r"\{(.*?)\}", block_match.group(1), re.S):
        obj = obj_match.group(1)
        row: dict[str, str] = {}
        for key in ("company", "role", "link", "location", "posted", "pay", "dates"):
            match = re.search(rf"{key}:\s*\"((?:\\.|[^\"])*)\"", obj)
            if match:
                row[key] = unescape_js_string(match.group(1))
        if row.get("company") and row.get("role") and row.get("link"):
            jobs.append(row)
    return jobs


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return unescape(value).strip()


def extract_raw_url_jobs(html: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    visible_html = re.sub(r"<script\b.*?</script>", "", html, flags=re.I | re.S)
    visible_html = re.sub(r"<style\b.*?</style>", "", visible_html, flags=re.I | re.S)
    text = unescape(re.sub(r"<br\s*/?>", "\n", visible_html, flags=re.I))
    text = re.sub(r"</(?:p|div|li|tr|h[1-6])>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    pattern = re.compile(
        r"Company:\s*(?P<company>.+?)\n\s*Role:\s*(?P<role>.+?)\n(?P<body>.*?)(?:\n\s*Company:|\Z)",
        re.S | re.I,
    )
    for match in pattern.finditer(text):
        body = match.group("body")
        url_match = re.search(r"Raw URL:\s*(https?://\S+)", body, re.I)
        if not url_match:
            url_match = re.search(r"Link:.*?(https?://\S+)", body, re.I | re.S)
        if url_match:
            jobs.append({
                "company": match.group("company").strip(),
                "role": match.group("role").strip(),
                "link": url_match.group(1).strip(),
            })
    return jobs


def extract_anchor_jobs(html: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    pattern = re.compile(
        r'<h3 class="job-title"><a href="([^"]+)".*?>(.*?)</a></h3>\s*'
        r'<div class="job-company">(.*?)</div>',
        re.S,
    )
    for link, role, company in pattern.findall(html):
        role = clean_text(role)
        company = clean_text(company)
        jobs.append({"company": company, "role": role, "link": link})
    return jobs


def dedupe(jobs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for job in jobs:
        key = (normalize(job["company"]), normalize(job["role"]), job["link"])
        if key not in seen:
            out.append(job)
            seen.add(key)
    return out


def find_matches(jobs: list[dict[str, str]], company: str, role: str) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for job in jobs:
        company_score = similarity(company, job.get("company", ""))
        role_score = similarity(role, job.get("role", ""))
        score = company_score + role_score
        if company_score >= 50 and role_score >= 35:
            matches.append({"score": score, **job})
    return sorted(matches, key=lambda item: int(item["score"]), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_file", help="Path to saved Handshake HTML")
    parser.add_argument("--company", help="Company name to match")
    parser.add_argument("--role", help="Role title to match")
    parser.add_argument("--list", action="store_true", help="List all extracted jobs")
    args = parser.parse_args()

    html_path = Path(args.html_file).expanduser()
    html = html_path.read_text(encoding="utf-8", errors="replace")
    jobs = dedupe(extract_raw_url_jobs(html) or extract_initial_jobs(html) or extract_anchor_jobs(html))

    if args.list or not (args.company and args.role):
        print(json.dumps({"count": len(jobs), "jobs": jobs}, indent=2))
        return 0

    matches = find_matches(jobs, args.company, args.role)
    print(json.dumps({"count": len(matches), "matches": matches}, indent=2))
    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
