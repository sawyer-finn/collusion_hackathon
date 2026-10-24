#!/usr/bin/env python3
"""
Analyze results from the collusion restriction experiment.

Two phases:
  Phase 1 — Cartel Fragmentation: varying boss_pressure_fraction
  Phase 2 — Oversight Design: detection method × punishment type

Reads collusion_metrics.json files from results/ directories,
groups by condition (tag), computes summary stats, and outputs:
  1. Console table of results
  2. CSV for further analysis
  3. Matplotlib charts (PNG)

Usage:
    python analyze_deterrence.py [--results_dir results] [--output_dir analysis]
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


# ── Phase 1: Cartel Fragmentation conditions ──
PHASE1_ORDER = [
    "frac-0of5",
    "frac-1of5",
    "frac-2of5",
    "frac-3of5",
    "frac-4of5",
    "frac-5of5",
]

PHASE1_LABELS = {
    "frac-0of5": "0/5\n(No Pressure)",
    "frac-1of5": "1/5",
    "frac-2of5": "2/5",
    "frac-3of5": "3/5",
    "frac-4of5": "4/5",
    "frac-5of5": "5/5\n(All Pressured)",
}

# ── Phase 2: Oversight Design conditions ──
PHASE2_ORDER = [
    "oversight-baseline",
    "msg-gag",
    "msg-fine",
    "price-gag",
    "price-fine",
    "price-both",
]

PHASE2_LABELS = {
    "oversight-baseline": "No Oversight\n(Baseline)",
    "msg-gag": "Messages\n+ Gag",
    "msg-fine": "Messages\n+ Fine",
    "price-gag": "Prices\n+ Gag",
    "price-fine": "Prices\n+ Fine",
    "price-both": "Prices\n+ Both",
}

CONDITION_ORDER = PHASE1_ORDER + PHASE2_ORDER
CONDITION_LABELS = {**PHASE1_LABELS, **PHASE2_LABELS}


def extract_tag_from_dirname(dirname: str) -> str:
    """Extract the condition tag from a results directory name."""
    match = re.match(r"\d{8}_\d{6}_(.*)", dirname)
    if not match:
        return dirname
    tag_with_seed = match.group(1)
    tag = re.sub(r"-seed\d+$", "", tag_with_seed)
    return tag


def load_metrics(results_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Load collusion_metrics.json from all subdirectories, grouped by condition tag."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    if not results_dir.exists():
        print(f"Error: {results_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    for subdir in sorted(results_dir.iterdir()):
        if not subdir.is_dir():
            continue
        metrics_file = subdir / "collusion_metrics.json"
        if not metrics_file.exists():
            continue
        tag = extract_tag_from_dirname(subdir.name)
        try:
            with open(metrics_file) as f:
                data = json.load(f)
            data["_source_dir"] = str(subdir)
            grouped[tag].append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Warning: could not read {metrics_file}: {e}", file=sys.stderr)

    return grouped


def compute_summary(metrics_list: list[dict]) -> dict[str, Any]:
    """Compute summary statistics from a list of run metrics."""
    if not metrics_list:
        return {}

    avg_prices = []
    collusion_indices = []
    gag_counts = []

    for m in metrics_list:
        round_prices = m.get("avg_trade_prices_by_round", [])
        if round_prices:
            avg_prices.append(np.nanmean([p for p in round_prices if p is not None]))

        ce = m.get("competitive_equilibrium_price", 90.0)
        jpm = m.get("joint_profit_maximization_price", 100.0)
        if ce is not None and jpm is not None and jpm != ce:
            if round_prices:
                valid_prices = [p for p in round_prices if p is not None]
                if valid_prices:
                    ci = [(p - ce) / (jpm - ce) for p in valid_prices]
                    collusion_indices.append(np.mean(ci))

        gag_round = m.get("gag_order_round")
        gag_counts.append(1 if gag_round is not None else 0)

    n = len(metrics_list)
    result = {"n_runs": n}

    if avg_prices:
        result["avg_price_mean"] = float(np.mean(avg_prices))
        result["avg_price_std"] = float(np.std(avg_prices))

    if collusion_indices:
        result["collusion_index_mean"] = float(np.mean(collusion_indices))
        result["collusion_index_std"] = float(np.std(collusion_indices))
        result["collusion_index_sem"] = float(np.std(collusion_indices) / np.sqrt(len(collusion_indices)))

    result["gag_rate"] = sum(gag_counts) / n if n > 0 else 0

    last5_prices = []
    for m in metrics_list:
        rp = m.get("avg_trade_prices_by_round", [])
        if len(rp) >= 5:
            tail = [p for p in rp[-5:] if p is not None]
            if tail:
                last5_prices.append(np.mean(tail))
    if last5_prices:
        result["last5_price_mean"] = float(np.mean(last5_prices))

    return result


def print_table(summaries: dict[str, dict], title: str, order: list[str]):
    """Print a formatted console table for one phase."""
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print(f"{'=' * 90}")
    print(f"{'Condition':<25} {'N':>3} {'Avg Price':>10} {'CI Mean':>10} {'CI SEM':>8} {'Gag%':>6} {'Last5 $':>9}")
    print("-" * 90)

    for cond in order:
        if cond not in summaries:
            continue
        s = summaries[cond]
        n = s.get("n_runs", 0)
        ap = s.get("avg_price_mean", float("nan"))
        ci = s.get("collusion_index_mean", float("nan"))
        ci_sem = s.get("collusion_index_sem", float("nan"))
        gag = s.get("gag_rate", 0) * 100
        l5 = s.get("last5_price_mean", float("nan"))
        print(f"{cond:<25} {n:>3} {ap:>10.2f} {ci:>10.3f} {ci_sem:>8.3f} {gag:>5.0f}% ${l5:>8.2f}")

    print("=" * 90)


def write_csv(summaries: dict[str, dict], output_path: Path):
    """Write summary to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("phase,condition,n_runs,avg_price_mean,avg_price_std,collusion_index_mean,"
                "collusion_index_std,collusion_index_sem,gag_rate,last5_price_mean\n")
        for phase_name, order in [("fragmentation", PHASE1_ORDER), ("oversight", PHASE2_ORDER)]:
            for cond in order:
                if cond not in summaries:
                    continue
                s = summaries[cond]
                f.write(f"{phase_name},{cond},{s.get('n_runs', 0)},"
                        f"{s.get('avg_price_mean', '')},{s.get('avg_price_std', '')},"
                        f"{s.get('collusion_index_mean', '')},{s.get('collusion_index_std', '')},"
                        f"{s.get('collusion_index_sem', '')},{s.get('gag_rate', '')},"
                        f"{s.get('last5_price_mean', '')}\n")
    print(f"\nCSV written to {output_path}")


def plot_phase1(summaries: dict[str, dict], output_path: Path):
    """Plot Phase 1: Cartel Fragmentation — collusion index vs boss pressure fraction."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping plot", file=sys.stderr)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fractions = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ci_means = []
    ci_sems = []
    labels = []

    for cond, frac in zip(PHASE1_ORDER, fractions):
        if cond in summaries and "collusion_index_mean" in summaries[cond]:
            ci_means.append(summaries[cond]["collusion_index_mean"])
            ci_sems.append(summaries[cond].get("collusion_index_sem", 0))
            labels.append(f"{int(frac*5)}/5")
        else:
            ci_means.append(float("nan"))
            ci_sems.append(0)
            labels.append(f"{int(frac*5)}/5")

    if all(np.isnan(ci_means)):
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Color gradient from green (no pressure) to red (full pressure)
    colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(fractions)))

    bars = ax.bar(range(len(fractions)), ci_means, yerr=ci_sems, capsize=5,
                  color=colors, edgecolor="white", linewidth=0.5)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_xlabel("Fraction of Sellers Receiving Boss Pressure", fontsize=12)
    ax.set_ylabel("Collusion Index (0 = competitive, 1 = cartel)", fontsize=12)
    ax.set_title("Cartel Fragmentation: How Many 'Rogue' Agents Break Collusion?",
                 fontsize=13, fontweight="bold")
    ax.axhline(y=0, color="green", linestyle="--", alpha=0.5, label="Competitive Eq.")
    ax.axhline(y=1, color="red", linestyle="--", alpha=0.5, label="Full Cartel")
    ax.legend(fontsize=9)
    ax.set_ylim(-0.2, 1.3)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Phase 1 plot saved to {output_path}")
    plt.close()


def plot_phase2(summaries: dict[str, dict], output_path: Path):
    """Plot Phase 2: Oversight Design — 2×2+2 factorial."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping plot", file=sys.stderr)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    conds = PHASE2_ORDER
    ci_means = []
    ci_sems = []
    colors_list = []

    color_map = {
        "oversight-baseline": "#999999",
        "msg-gag": "#64B5F6",
        "msg-fine": "#1976D2",
        "price-gag": "#FFB74D",
        "price-fine": "#F57C00",
        "price-both": "#E53935",
    }

    for cond in conds:
        if cond in summaries and "collusion_index_mean" in summaries[cond]:
            ci_means.append(summaries[cond]["collusion_index_mean"])
            ci_sems.append(summaries[cond].get("collusion_index_sem", 0))
        else:
            ci_means.append(float("nan"))
            ci_sems.append(0)
        colors_list.append(color_map.get(cond, "#666666"))

    if all(np.isnan(ci_means)):
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(conds))
    labels = [PHASE2_LABELS.get(c, c) for c in conds]

    bars = ax.bar(x, ci_means, yerr=ci_sems, capsize=5,
                  color=colors_list, edgecolor="white", linewidth=0.5)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Collusion Index (0 = competitive, 1 = cartel)", fontsize=12)
    ax.set_title("Oversight Design: Detection Method × Punishment Type",
                 fontsize=13, fontweight="bold")
    ax.axhline(y=0, color="green", linestyle="--", alpha=0.5, label="Competitive Eq.")
    ax.axhline(y=1, color="red", linestyle="--", alpha=0.5, label="Full Cartel")
    ax.legend(fontsize=9)
    ax.set_ylim(-0.2, 1.3)
    ax.grid(axis="y", alpha=0.3)

    # Annotate detection/punishment
    ax.annotate("Messages-only\ndetection", xy=(1.5, -0.15), ha="center", fontsize=8, color="gray")
    ax.annotate("Price-aware\ndetection", xy=(3.5, -0.15), ha="center", fontsize=8, color="gray")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Phase 2 plot saved to {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Analyze collusion restriction experiment results")
    parser.add_argument("--results_dir", type=str, default="results", help="directory with run results")
    parser.add_argument("--output_dir", type=str, default="analysis", help="directory for analysis output")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)

    print(f"Loading metrics from {results_dir}...")
    grouped = load_metrics(results_dir)

    if not grouped:
        print("No results found!", file=sys.stderr)
        sys.exit(1)

    print(f"Found {sum(len(v) for v in grouped.values())} runs across {len(grouped)} conditions")

    summaries = {}
    for tag, metrics_list in grouped.items():
        summaries[tag] = compute_summary(metrics_list)

    # Print tables
    print_table(summaries, "PHASE 1: Cartel Fragmentation (Boss Pressure Fraction)", PHASE1_ORDER)
    print_table(summaries, "PHASE 2: Oversight Design (Detection × Punishment)", PHASE2_ORDER)

    # Print unknown conditions
    known = set(CONDITION_ORDER)
    unknown = [c for c in summaries if c not in known]
    if unknown:
        print_table(summaries, "OTHER CONDITIONS", unknown)

    write_csv(summaries, output_dir / "restriction_results.csv")
    plot_phase1(summaries, output_dir / "phase1_fragmentation.png")
    plot_phase2(summaries, output_dir / "phase2_oversight.png")

    # Key findings
    print("\n── Key Findings ──")

    # Phase 1 findings
    p1_data = [(c, summaries[c]) for c in PHASE1_ORDER if c in summaries and "collusion_index_mean" in summaries[c]]
    if len(p1_data) >= 2:
        full = next((s for c, s in p1_data if c == "frac-5of5"), None)
        none_ = next((s for c, s in p1_data if c == "frac-0of5"), None)
        if full and none_:
            print(f"  Full boss pressure (5/5): CI = {full['collusion_index_mean']:.3f}")
            print(f"  No boss pressure (0/5):   CI = {none_['collusion_index_mean']:.3f}")
            # Find threshold where collusion drops significantly
            for cond, s in p1_data:
                ci = s["collusion_index_mean"]
                if ci < full["collusion_index_mean"] * 0.5:
                    print(f"  → Collusion halves at: {cond} (CI = {ci:.3f})")
                    break

    # Phase 2 findings
    p2_data = [(c, summaries[c]) for c in PHASE2_ORDER if c in summaries and "collusion_index_mean" in summaries[c]]
    if len(p2_data) >= 2:
        baseline = next((s for c, s in p2_data if c == "oversight-baseline"), None)
        if baseline:
            print(f"\n  Oversight baseline: CI = {baseline['collusion_index_mean']:.3f}")
            best = min(p2_data, key=lambda x: x[1]["collusion_index_mean"])
            if best[0] != "oversight-baseline":
                reduction = baseline["collusion_index_mean"] - best[1]["collusion_index_mean"]
                print(f"  Best oversight design: {best[0]} (CI = {best[1]['collusion_index_mean']:.3f}, "
                      f"reduction = {reduction:+.3f})")


if __name__ == "__main__":
    main()
