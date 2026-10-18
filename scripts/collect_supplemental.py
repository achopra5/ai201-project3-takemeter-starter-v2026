#!/usr/bin/env python3
"""Fetch separate public archive scan pages; never replace the frozen collection.

This retrieves raw evidence and a title catalog, NOT labels or verification.
An annotator must read each full title/body before proposing a supplemental row.
Output directories must be new; this command cannot overwrite a prior scan.
"""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "pszemraj/LocalLLaMA-posts"


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "TakeMeter-supplement/1.0"}), timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offsets", type=int, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("output directory already exists; use a new supplemental scan directory")
    if len(set(args.offsets)) != len(args.offsets) or min(args.offsets) < 0:
        parser.error("offsets must be distinct nonnegative integers")
    urls = ["https://datasets-server.huggingface.co/rows?" + urlencode(dict(
        dataset=DATASET, config="default", split="train", offset=offset, length=100)) for offset in args.offsets]
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(fetch, urls))
    # Fetch first, then create a fresh directory so failed requests do not leave
    # a misleading complete scan. Full responses are retained without truncation.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    sources, catalog = [], []
    for offset, url, raw in zip(args.offsets, urls, pages):
        filename = f"rows-{offset}.json"
        (args.output_dir / filename).write_bytes(raw)
        page = json.loads(raw)
        sources.append(dict(offset=offset, request_url=url, file=filename,
                            sha256=hashlib.sha256(raw).hexdigest(), rows=len(page["rows"])))
        for item in page["rows"]:
            r = item["row"]
            catalog.append(dict(row_idx=item["row_idx"], source_id=r["id"], title=r["title"],
                                body_chars=len(r.get("selftext") or ""), raw_file=filename))
    manifest = dict(dataset=DATASET, config="default", split="train",
                    retrieved_utc=datetime.now(timezone.utc).isoformat(), sources=sources,
                    purpose="Targeted supplemental technical-report candidate search; no labels assigned by collection.",
                    original_collection_rerun=False, truncation="None: exact API response bytes retained")
    (args.output_dir / "scan_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(catalog)} raw scan rows to {args.output_dir}; none are labeled or human-verified.")
    for item in catalog:
        if item["body_chars"] >= 150:
            print(item["row_idx"], item["source_id"], item["body_chars"], item["title"])


if __name__ == "__main__":
    main()
