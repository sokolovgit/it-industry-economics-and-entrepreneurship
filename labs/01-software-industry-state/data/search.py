"""Пошук первинних досліджень через відкриті API OpenAlex і arXiv.

Для кожного пошукового рядка фіксуємо кількість знайдених публікацій і зберігаємо
записи для скринінгу. Результат відтворюваний: ті самі запити дають ті самі цифри
на дату пошуку (вона пишеться у search_log.json).
"""

import csv
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
MAILTO = "student@kpi.ua"
YEARS = ("2022-01-01", "2026-12-31")

# Пошукові рядки протоколу: S1 – продуктивність, S2 – експериментальні дизайни,
# S3 – якість і безпека коду.
QUERIES = {
    "S1": '("GitHub Copilot" OR "AI coding assistant" OR "AI pair programmer" OR "AI tools" OR "AI assistance" OR "generative AI") '
    'AND ("developer productivity" OR "programmer productivity" OR "software development productivity")',
    "S2": '("generative AI" OR "large language model" OR "LLM" OR "Copilot") AND ("software development" OR "software engineering") '
    'AND ("randomized controlled trial" OR "field experiment" OR "controlled experiment")',
    "S3": '("GitHub Copilot" OR "AI coding assistant" OR "AI-generated code" OR "LLM-generated code") '
    'AND ("code quality" OR "defects" OR "bugs" OR "security vulnerabilities")',
}

ARXIV = {
    "S1": '(abs:"GitHub Copilot" OR abs:"AI coding assistant" OR abs:"AI pair programmer" OR abs:"AI tools") AND abs:"developer productivity"',
    "S2": '(abs:"large language model" OR abs:"Copilot" OR abs:"generative AI") AND abs:"software development" '
    'AND (abs:"randomized controlled trial" OR abs:"field experiment" OR abs:"controlled experiment")',
    "S3": '(abs:"GitHub Copilot" OR abs:"AI coding assistant" OR abs:"AI-generated code") '
    'AND (abs:"code quality" OR abs:"security" OR abs:"bugs")',
}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"kpi-slr ({MAILTO})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def openalex(query: str, pages: int = 5) -> tuple[int, list[dict]]:
    flt = f"title_and_abstract.search:{query},from_publication_date:{YEARS[0]},to_publication_date:{YEARS[1]}"
    rows, total = [], 0
    for page in range(1, pages + 1):
        params = {
            "filter": flt,
            "per-page": 200,
            "page": page,
            "mailto": MAILTO,
            "select": "id,doi,title,publication_year,type,cited_by_count,primary_location",
        }
        data = json.loads(
            get("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
        )
        total = data["meta"]["count"]
        for w in data["results"]:
            src = ((w.get("primary_location") or {}).get("source") or {}).get(
                "display_name"
            ) or ""
            rows.append(
                {
                    "db": "OpenAlex",
                    "id": w["id"],
                    "doi": w.get("doi") or "",
                    "title": w.get("title") or "",
                    "year": w.get("publication_year"),
                    "type": w.get("type"),
                    "venue": src,
                    "cited": w.get("cited_by_count", 0),
                }
            )
        if page * 200 >= total:
            break
        time.sleep(1)
    return total, rows


def arxiv(query: str, n: int = 300) -> tuple[int, list[dict]]:
    q = f"({query}) AND submittedDate:[202201010000 TO 202612312359]"
    params = {"search_query": q, "start": 0, "max_results": n}
    root = ET.fromstring(
        get("http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params))
    )
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "os": "http://a9.com/-/spec/opensearch/1.1/",
    }
    total = int(root.find("os:totalResults", ns).text)
    rows = []
    for e in root.findall("a:entry", ns):
        rows.append(
            {
                "db": "arXiv",
                "id": e.find("a:id", ns).text,
                "doi": "",
                "title": " ".join(e.find("a:title", ns).text.split()),
                "year": int(e.find("a:published", ns).text[:4]),
                "type": "preprint",
                "venue": "arXiv",
                "cited": "",
            }
        )
    return total, rows


def main():
    log = {"date": dt.date.today().isoformat(), "years": YEARS, "queries": {}}
    allrows = []
    for key, q in QUERIES.items():
        n, rows = openalex(q)
        log["queries"][key] = {"openalex_query": q, "openalex": n}
        allrows += [dict(r, query=key) for r in rows]
        time.sleep(1)
        m, rows = arxiv(ARXIV[key])
        log["queries"][key].update({"arxiv_query": ARXIV[key], "arxiv": m})
        allrows += [dict(r, query=key) for r in rows]
        time.sleep(3)
        print(f"{key}: OpenAlex {n}, arXiv {m}")
    (HERE / "search_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with open(HERE / "records.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "query",
                "db",
                "id",
                "doi",
                "title",
                "year",
                "type",
                "venue",
                "cited",
            ],
        )
        w.writeheader()
        w.writerows(allrows)
    print(f"записів збережено: {len(allrows)}")


if __name__ == "__main__":
    main()
