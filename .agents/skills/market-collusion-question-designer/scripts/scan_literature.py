#!/usr/bin/env python3
"""Search the sprint repository's literature map without external dependencies."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def find_catalog(start: Path) -> Path:
    candidates = [start.resolve(), *start.resolve().parents, Path(__file__).resolve().parent]
    seen: set[Path] = set()
    for base in candidates:
        for directory in [base, *base.parents]:
            if directory in seen:
                continue
            seen.add(directory)
            catalog = directory / "literature" / "papers.csv"
            if catalog.is_file():
                return catalog
    raise FileNotFoundError("Could not find literature/papers.csv from the current repository.")


def normalize(value: str | None) -> str:
    return (value or "").strip()


def project_matches(projects: str, requested: list[str]) -> bool:
    if not requested:
        return True
    tags = {tag.strip() for tag in projects.split(";") if tag.strip()}
    return any(project in tags for project in requested)


def query_score(row: dict[str, str], terms: list[str]) -> int:
    if not terms:
        return 1
    weighted = [
        (normalize(row.get("title")).lower(), 6),
        (normalize(row.get("citation")).lower(), 4),
        (normalize(row.get("summary")).lower(), 2),
        (normalize(row.get("field")).lower(), 1),
        (normalize(row.get("authors")).lower(), 1),
    ]
    score = 0
    for term in terms:
        term_score = max((weight for text, weight in weighted if term in text), default=0)
        score += term_score
    return score


def compact(text: str, width: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1].rstrip() + "…"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Filter and rank literature/papers.csv for a sprint subtrack or mechanism."
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Exact sprint tag such as 1.5. Repeat to include multiple tags.",
    )
    parser.add_argument(
        "--query",
        default="",
        help="Space-separated search terms matched across title, citation, summary, field, and authors.",
    )
    parser.add_argument("--year-min", type=int, default=None)
    parser.add_argument("--on-sprint-page", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=("markdown", "tsv"), default="markdown")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="Override the path to papers.csv.",
    )
    args = parser.parse_args()

    try:
        catalog = args.catalog.resolve() if args.catalog else find_catalog(Path.cwd())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    terms = [term.lower() for term in args.query.split() if term.strip()]
    results: list[tuple[int, int, dict[str, str]]] = []
    with catalog.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not project_matches(normalize(row.get("sprint_projects")), args.project):
                continue
            try:
                year = int(normalize(row.get("year")) or 0)
            except ValueError:
                year = 0
            if args.year_min is not None and year < args.year_min:
                continue
            if args.on_sprint_page and normalize(row.get("on_sprint_page")).lower() != "yes":
                continue
            score = query_score(row, terms)
            if terms and score == 0:
                continue
            if normalize(row.get("on_sprint_page")).lower() == "yes":
                score += 1
            results.append((score, year, row))

    results.sort(key=lambda item: (-item[0], -item[1], normalize(item[2].get("citation"))))
    results = results[: max(args.limit, 0)]

    if args.format == "tsv":
        print("score\tid\tyear\tcitation\ttitle\tprojects\tfield\tsummary\turl")
        for score, year, row in results:
            values = [
                str(score),
                normalize(row.get("id")),
                str(year or ""),
                normalize(row.get("citation")),
                normalize(row.get("title")),
                normalize(row.get("sprint_projects")),
                normalize(row.get("field")),
                compact(normalize(row.get("summary"))),
                normalize(row.get("url")),
            ]
            print("\t".join(value.replace("\t", " ") for value in values))
        return 0

    print(f"Catalog: `{catalog}`")
    filters = []
    if args.project:
        filters.append("projects=" + ",".join(args.project))
    if terms:
        filters.append("query=" + " ".join(terms))
    if args.year_min is not None:
        filters.append(f"year>={args.year_min}")
    if args.on_sprint_page:
        filters.append("sprint-page-only")
    print("Filters: " + (", ".join(filters) if filters else "none"))
    print()
    print("| Score | Year | Paper | Projects | Field | Why relevant |")
    print("|---:|---:|---|---|---|---|")
    for score, year, row in results:
        citation = normalize(row.get("citation")) or normalize(row.get("title"))
        title = normalize(row.get("title"))
        label = citation if citation == title or not title else f"{citation} — *{title}*"
        url = normalize(row.get("url"))
        paper = f"[{label}]({url})" if url else label
        cells = [
            str(score),
            str(year or ""),
            paper,
            normalize(row.get("sprint_projects")) or "—",
            normalize(row.get("field")) or "—",
            compact(normalize(row.get("summary"))).replace("|", "\\|"),
        ]
        print("| " + " | ".join(cells) + " |")
    if not results:
        print("| — | — | No matching papers | — | — | Broaden the query or project tags. |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
