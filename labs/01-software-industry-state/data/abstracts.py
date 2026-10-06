"""Скринінг за анотаціями: емпіричне дослідження з кількісним результатом.

Анотації беруться з OpenAlex (abstract_inverted_index) і arXiv. Дослідження проходить,
якщо в анотації є емпіричний дизайн з людьми-розробниками або реальними репозиторіями
і кількісний результат, і немає ознак статті-пропозиції нового методу.
"""

import csv
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
CACHE = HERE / "abstracts_cache.json"

EMPIRICAL = re.compile(
    r"randomi[sz]ed|controlled (?:trial|experiment)|field experiment|experiment|participants|"
    r"\d[\d,]*\+? (?:\w+ ){0,2}(?:developers|engineers|programmers|repositories|projects|commits|users|programs|code samples|pull requests|tasks)|"
    r"difference-in-differences|quasi-experiment|telemetry|longitudinal|case study|natural experiment",
    re.I,
)
QUANT = re.compile(
    r"\d+(?:\.\d+)?\s?%|percent|percentage points|\bp\s?[<=]|confidence interval|statistically significant",
    re.I,
)
PROPOSAL = re.compile(
    r"\bwe propose\b|\bwe present a (?:novel|new) (?:approach|framework|method|tool|technique)|"
    r"\bour (?:approach|framework|tool|method) (?:achieves|outperforms)|\boutperforms\b|fine-tun",
    re.I,
)


def get(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "kpi-slr (student@kpi.ua)"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def abstract(row: dict, cache: dict) -> str:
    key = row["id"]
    if key in cache:
        return cache[key]
    text = ""
    if row["db"] == "OpenAlex":
        wid = key.rsplit("/", 1)[-1]
        d = json.loads(
            get(
                f"https://api.openalex.org/works/{wid}?mailto=student@kpi.ua&select=abstract_inverted_index"
            )
        )
        inv = d.get("abstract_inverted_index") or {}
        text = " ".join(
            w for _, w in sorted((p, w) for w, ps in inv.items() for p in ps)
        )
        time.sleep(0.15)
    else:
        aid = key.rsplit("/abs/", 1)[-1]
        root = ET.fromstring(
            get(
                "http://export.arxiv.org/api/query?"
                + urllib.parse.urlencode({"id_list": aid})
            )
        )
        node = root.find(
            "{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}summary"
        )
        text = " ".join((node.text or "").split()) if node is not None else ""
        time.sleep(3)
    cache[key] = text
    return text


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    rows = list(csv.DictReader(open(HERE / "candidates.csv", encoding="utf-8")))
    passed, reasons = (
        [],
        {
            "no_abstract_to_fulltext": 0,
            "not_empirical": 0,
            "no_quantitative_result": 0,
            "method_proposal": 0,
        },
    )
    for r in rows:
        text = abstract(r, cache)
        if not text:
            # без анотації рішення приймається за повним текстом
            reasons["no_abstract_to_fulltext"] += 1
            passed.append(r)
        elif PROPOSAL.search(text):
            reasons["method_proposal"] += 1
        elif not EMPIRICAL.search(text):
            reasons["not_empirical"] += 1
        elif not QUANT.search(text):
            reasons["no_quantitative_result"] += 1
        else:
            passed.append(r)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    with open(HERE / "fulltext.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(passed)
    log = json.loads((HERE / "screen_log.json").read_text())
    log.update(
        {
            "abstract_screened": len(rows),
            "abstract_passed": len(passed),
            "abstract_excluded": reasons,
        }
    )
    (HERE / "screen_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
