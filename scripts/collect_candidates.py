#!/usr/bin/env python3
"""Collect unlabelled, complete r/LocalLLaMA text posts from public HF archive.

Source: https://huggingface.co/datasets/pszemraj/LocalLLaMA-posts (ODC-BY).
Do not mistake candidates for human-labeled training examples.
"""
import argparse, csv, json, random, re, sys, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "pszemraj/LocalLLaMA-posts"
API = "https://datasets-server.huggingface.co"

def get(endpoint, params):
    url = f"{API}/{endpoint}?{urlencode(params)}"
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent":"TakeMeter-AI201/0.1", "Accept":"application/json"})
            with urlopen(request, timeout=45) as response:
                return json.load(response)
        except Exception as exc:
            if attempt == 2: raise RuntimeError(f"Could not fetch {url}: {exc}") from exc
            time.sleep(2 * (attempt+1))

def eligible(r):
    title = (r.get("title") or "").strip()
    body = (r.get("selftext") or "").strip()
    if not title or len(body) < 80 or len(body) > 12000: return None
    if body.lower() in ("[deleted]", "[removed]", "deleted", "removed"): return None
    if len(re.sub(r"https?://\S+", "", body).strip()) < 65: return None
    rid = str(r.get("id") or "").strip()
    permalink = str(r.get("permalink") or "").strip()
    if not rid:
        match = re.search(r"/comments/([^/]+)/", permalink)
        rid = match.group(1) if match else ""
    if not rid: return None
    url = ("https://www.reddit.com" + permalink) if permalink.startswith("/r/") else f"https://www.reddit.com/r/LocalLLaMA/comments/{rid}/"
    return {"text":title+"\n\n"+body, "source_url":url, "source_id":rid,
            "created_utc":str(r.get("created") or ""), "source_dataset":DATASET}

def output(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows: writer.writerow({col:row.get(col,"") for col in columns})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target",type=int,default=320)
    parser.add_argument("--max-pages",type=int,default=40)
    args=parser.parse_args()
    if args.target < 200: parser.error("--target must be at least 200")
    info=get("splits", {"dataset":DATASET})["splits"]
    trains=[s for s in info if s["split"]=="train"]
    conf=next((s for s in trains if s["config"]=="default"),trains[0])
    total=int(conf["num_examples"])
    found={}
    scanned=0
    for i in range(args.max_pages):
        offset=max(0,total-100*(i+1))
        page=get("rows", {"dataset":DATASET,"config":conf["config"],"split":"train",
                          "offset":offset,"length":min(100,total-offset)})
        for wrapper in page["rows"]:
            candidate=eligible(wrapper["row"])
            if candidate: found.setdefault(candidate["source_id"],candidate)
        scanned += 1
        print(f"Scanned {scanned} pages; {len(found)} usable, distinct posts",file=sys.stderr)
        if len(found)>=int(args.target*1.35) or offset==0: break
    rng=random.Random(20261018)
    rows=list(found.values())
    rng.shuffle(rows)
    if len(rows)<args.target:
        raise RuntimeError(f"Only found {len(rows)} candidates; increase --max-pages.")
    rows=rows[:args.target]
    output(Path("data/candidate_posts.csv"), rows,
           ["text","source_url","source_id","created_utc","source_dataset"])
    queue=[{"text":r["text"],"label":"",
            "note":"cold — label unaided" if i<20 else "unlabeled — review later",
            "source_url":r["source_url"]} for i,r in enumerate(rows)]
    output(Path("data/annotation_queue.csv"),queue,["text","label","note","source_url"])
    manifest={"dataset":DATASET,"archive_posts":total,"pages_scanned":scanned,
              "n_candidates":len(rows),"seed":20261018,
              "collected_utc":datetime.now(timezone.utc).isoformat(),
              "archive_updated_through":"2026-03-03",
              "labels":"NONE — all annotations remain pending",
              "selection":"Full text only, complete title+body, no truncation, no link-only posts."}
    Path("data/candidate_posts.manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"Collected {len(rows)} authentic UNLABELLED posts; first 20 must be cold-labeled by student.")
    print("When every row is reviewed and assigned a label, export only text,label,note to labels.csv.")

if __name__=="__main__":
    main()
