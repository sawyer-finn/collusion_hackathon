"""Starvation curve: does an early lack of sales predict the cartel's later collapse?

Predictor: share of LLM-seller-rounds with a sale in rounds 1-5 (first third).
Outcome: LLM-seller ask index in the last third of rounds (as everywhere else in FINDINGS.md).
Runs are selected by `auction_config.tag` in experiment_metadata.json, never by folder name.

Usage: uv run python experiments/starvation_curve.py [--out results/starvation_runs.csv]
"""

import argparse
import csv
import glob
import json
import os
import re

import numpy as np

# (tag, market, n_entrants); gpt-4.1 sellers + gpt-4.1-mini buyers only, 5x10 left out (not in the report)
CONDITIONS = [
    ("control41", "5x5", 0),
    ("c8_random", "5x5", 1),
    ("c9_noregret1", "5x5", 1),
    ("c8b_random2", "5x5", 2),
    ("c10_noregret2", "5x5", 2),
    ("c11_mixed", "5x5", 2),
    ("q7_control", "7x7", 0),
    ("q7_noregret1", "7x7", 1),
    ("q7_noregret2", "7x7", 2),
    ("q7_noregret3", "7x7", 3),
]
EARLY = range(1, 6)  # rounds 1-5; override with --early_rounds
JSON_BLOCK = re.compile(r"````json\n(.*?)\n````", re.S)


def load_rounds(run_dir):
    with open(os.path.join(run_dir, "auction_results.md")) as f:
        return [json.loads(block) for block in JSON_BLOCK.findall(f.read())]


def run_row(run_dir, tag, market, n_entrants):
    meta = json.load(open(os.path.join(run_dir, "experiment_metadata.json")))
    metrics = json.load(open(os.path.join(run_dir, "collusion_metrics.json")))
    entrants = set(meta.get("entrant_ids") or [])
    llm_sellers = [s for s in meta["seller_ids"] if s not in entrants]
    rounds = load_rounds(run_dir)

    early = [r for r in rounds if r["round_number"] in EARLY]
    sold = {(r["round_number"], t["seller_id"]) for r in early for t in r["trades"]}
    llm_sale_rate = sum((r["round_number"], s) in sold for r in early for s in llm_sellers) / (len(early) * len(llm_sellers))
    early_trades = [t for r in early for t in r["trades"]]
    entrant_share = (sum(t["seller_id"] in entrants for t in early_trades) / len(early_trades)) if early_trades else np.nan

    # runs from before the entrant code lack the LLM-seller key; with no entrants the two are identical
    idx = metrics.get("collusion_indices_avg_llm_seller_asks") or metrics["collusion_indices_avg_seller_asks"]
    k = len(idx) // 3
    return dict(
        tag=tag, market=market, n_entrants=n_entrants, seed=meta["auction_config"]["seed"],
        llm_sale_rate_early=llm_sale_rate, entrant_trade_share_early=entrant_share,
        early_trades=len(early_trades), index_last_third=float(np.mean(idx[-k:])), run_dir=os.path.basename(run_dir),
    )


def collect():
    by_tag = {tag: (market, n) for tag, market, n in CONDITIONS}
    rows = []
    for meta_path in sorted(glob.glob("results/*/experiment_metadata.json")):
        run_dir = os.path.dirname(meta_path)
        if not os.path.exists(os.path.join(run_dir, "collusion_metrics.json")):
            continue  # crashed run (see Dead ends)
        tag = json.load(open(meta_path))["auction_config"].get("tag", "").rsplit("-seed", 1)[0]
        if tag in by_tag:
            rows.append(run_row(run_dir, tag, *by_tag[tag]))
    return rows


def bootstrap(stat, rows, n=5000, seed=42):
    rng = np.random.default_rng(seed)
    vals = [stat([rows[i] for i in rng.integers(0, len(rows), len(rows))]) for _ in range(n)]
    return stat(rows), np.nanpercentile(vals, 2.5), np.nanpercentile(vals, 97.5)


def spearman(rows, x="llm_sale_rate_early", y="index_last_third"):
    a, b = np.array([r[x] for r in rows]), np.array([r[y] for r in rows])
    rank = lambda v: np.argsort(np.argsort(v)).astype(float)
    return float(np.corrcoef(rank(a), rank(b))[0, 1])


def ols(rows, cols):
    """Index on [1, cols...]; returns coefficients."""
    X = np.column_stack([np.ones(len(rows))] + [[r[c] for r in rows] for c in cols])
    y = np.array([r["index_last_third"] for r in rows])
    return np.linalg.lstsq(X, y, rcond=None)[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="results/starvation_runs.csv")
    p.add_argument("--early_rounds", type=int, nargs=2, metavar=("FIRST", "LAST"), help="predictor window, inclusive")
    args = p.parse_args()
    if args.early_rounds:
        global EARLY
        EARLY = range(args.early_rounds[0], args.early_rounds[1] + 1)

    rows = collect()
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} runs -> {args.out}\n")

    print(f"{'tag':16s} {'n':>3s} {'LLM sale rate':>20s} {'entrant share':>20s} {'index last third':>17s}")
    for tag, _, _ in CONDITIONS:
        rs = [r for r in rows if r["tag"] == tag]
        if rs:
            m = lambda k: f"{np.nanmean([r[k] for r in rs]):.2f}"
            print(f"{tag:16s} {len(rs):3d} {m('llm_sale_rate_early'):>20s} {m('entrant_trade_share_early'):>20s} {m('index_last_third'):>17s}")

    fmt = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
    print("\nSpearman(early LLM sale rate, last-third index), bootstrap over runs:")
    print("  all runs:", fmt(bootstrap(spearman, rows)))
    for n in sorted({r["n_entrants"] for r in rows}):
        rs = [r for r in rows if r["n_entrants"] == n]
        if len(rs) >= 5:
            print(f"  {n} entrant(s), n={len(rs)}:", fmt(bootstrap(spearman, rs)))

    # Does entrant count still predict the index once early starvation is accounted for?
    print("\nOLS index ~ 1 + early LLM sale rate + n_entrants (bootstrap over runs):")
    for i, name in [(1, "early LLM sale rate"), (2, "n_entrants")]:
        print(f"  {name}: {fmt(bootstrap(lambda rs: ols(rs, ['llm_sale_rate_early', 'n_entrants'])[i], rows))}")
    print("OLS index ~ 1 + n_entrants alone:")
    print(f"  n_entrants: {fmt(bootstrap(lambda rs: ols(rs, ['n_entrants'])[1], rows))}")


if __name__ == "__main__":
    main()
