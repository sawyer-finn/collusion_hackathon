#!/usr/bin/env python3
"""
Analyze results from the deterrence curve experiment.

Reads collusion_metrics.json files from results/ directories,
groups by condition (tag), computes summary stats, and outputs:
  1. Console table of results
  2. CSV for further analysis
  3. Matplotlib deterrence curve chart (PNG)

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

# ── Condition metadata ──────────────────────────────────────────────

CONDITION_ORDER = [
    "base-no-comms",
    "base-comms",
    "deter-vague",
    "deter-moderate",
    "deter-severe",
    "deter-prob",
    "deter-demonstrated",
    "deter-transparency",
    "oversight-comms",
    "overseer-price-aware",
    "overseer-price-only",
    "overseer-orderbook",
    "deter-severe+oversight",
]

CONDITION_LABELS = {
    "base-no-comms": "No Comms\n(Baseline)",
    "base-comms": "Comms\n(No Restriction)",
    "deter-vague": "Vague\nDeterrence",
    "deter-moderate": "Moderate\nDeterrence",
    "deter-severe": "Severe\nDeterrence",
    "deter-prob": "Probabilistic\nDeterrence",
    "deter-demonstrated": "Demonstrated\nDeterrence",
    "deter-transparency": "Transparency\nDeterrence",
    "oversight-comms": "LLM Oversight\n(Messages Only)",
    "overseer-price-aware": "LLM Oversight\n(Msgs + Prices)",
    "overseer-price-only": "LLM Oversight\n(Prices Only)",
    "overseer-orderbook": "LLM Oversight\n(Order Book)",
    "deter-severe+oversight": "Severe Deter.\n+ Oversight",
}

# Approximate per-run cost in USD (paper config, 3 seeds avg)
# Deterrence = 0 extra cost (prompt only), oversight adds overseer calls
CONDITION_COSTS = {
    "base-no-comms": 0.0,
    "base-comms": 0.0,
    "deter-vague": 0.0,
    "deter-moderate": 0.0,
    "deter-severe": 0.0,
    "deter-prob": 0.0,
    "deter-demonstrated": 0.0,
    "deter-transparency": 0.0,
    "oversight-comms": 1.0,  # ~30 extra overseer calls × ~$0.033
    "overseer-price-aware": 1.2,  # extended prompt slightly longer
    "overseer-price-only": 1.2,
    "overseer-orderbook": 1.0,
    "deter-severe+oversight": 1.0,
}


def extract_tag_from_dirname(dirname: str) -> str:
    """Extract the condition tag from a results directory name.

    Format: YYYYMMDD_HHMMSS_<tag>-seed<N>  or  YYYYMMDD_HHMMSS_<tag>
    """
    # Strip timestamp prefix
    match = re.match(r"\d{8}_\d{6}_(.*)", dirname)
    if not match:
        return dirname
    tag_with_seed = match.group(1)
    # Strip -seed<N> suffix
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
        # Average trade price across all rounds
        round_prices = m.get("avg_trade_prices_by_round", [])
        if round_prices:
            avg_prices.append(np.nanmean([p for p in round_prices if p is not None]))

        # Collusion index: (avg_price - CE) / (JPM - CE)
        ce = m.get("competitive_equilibrium_price", 90.0)
        jpm = m.get("joint_profit_maximization_price", 100.0)
        if ce is not None and jpm is not None and jpm != ce:
            if round_prices:
                valid_prices = [p for p in round_prices if p is not None]
                if valid_prices:
                    ci = [(p - ce) / (jpm - ce) for p in valid_prices]
                    collusion_indices.append(np.mean(ci))

        # Gag order triggered?
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

    # Last-5-rounds price (convergence indicator)
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


def print_table(grouped: dict[str, list[dict]], summaries: dict[str, dict]):
    """Print a formatted console table."""
    print("\n" + "=" * 100)
    print(f"{'Condition':<28} {'N':>3} {'Avg Price':>10} {'CI Mean':>10} {'CI SEM':>8} {'Gag%':>6} {'Last5 $':>9} {'Cost/run':>9}")
    print("-" * 100)

    for cond in CONDITION_ORDER:
        if cond not in summaries:
            continue
        s = summaries[cond]
        label = cond
        n = s.get("n_runs", 0)
        ap = s.get("avg_price_mean", float("nan"))
        ci = s.get("collusion_index_mean", float("nan"))
        ci_sem = s.get("collusion_index_sem", float("nan"))
        gag = s.get("gag_rate", 0) * 100
        l5 = s.get("last5_price_mean", float("nan"))
        cost = CONDITION_COSTS.get(cond, 0)

        print(f"{label:<28} {n:>3} {ap:>10.2f} {ci:>10.3f} {ci_sem:>8.3f} {gag:>5.0f}% ${l5:>8.2f} ${cost:>7.2f}")

    # Print any unknown conditions
    for cond in sorted(summaries.keys()):
        if cond not in CONDITION_ORDER:
            s = summaries[cond]
            n = s.get("n_runs", 0)
            ap = s.get("avg_price_mean", float("nan"))
            ci = s.get("collusion_index_mean", float("nan"))
            ci_sem = s.get("collusion_index_sem", float("nan"))
            gag = s.get("gag_rate", 0) * 100
            l5 = s.get("last5_price_mean", float("nan"))
            print(f"{'* ' + cond:<28} {n:>3} {ap:>10.2f} {ci:>10.3f} {ci_sem:>8.3f} {gag:>5.0f}% ${l5:>8.2f} ${'?':>7}")

    print("=" * 100)


def write_csv(summaries: dict[str, dict], output_path: Path):
    """Write summary to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("condition,n_runs,avg_price_mean,avg_price_std,collusion_index_mean,collusion_index_std,collusion_index_sem,gag_rate,last5_price_mean,cost_per_run\n")
        for cond in CONDITION_ORDER:
            if cond not in summaries:
                continue
            s = summaries[cond]
            f.write(f"{cond},{s.get('n_runs', 0)},{s.get('avg_price_mean', '')},{s.get('avg_price_std', '')},"
                    f"{s.get('collusion_index_mean', '')},{s.get('collusion_index_std', '')},"
                    f"{s.get('collusion_index_sem', '')},{s.get('gag_rate', '')},"
                    f"{s.get('last5_price_mean', '')},{CONDITION_COSTS.get(cond, '')}\n")
    print(f"\nCSV written to {output_path}")


def plot_deterrence_curve(summaries: dict[str, dict], output_path: Path):
    """Plot the deterrence curve: collusion index vs. condition."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping plot", file=sys.stderr)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Figure 1: Full comparison bar chart ──
    fig, ax = plt.subplots(figsize=(16, 7))

    conditions = []
    ci_means = []
    ci_sems = []
    colors_list = []

    color_map = {
        "base": "#666666",
        "deter": "#2196F3",
        "oversight": "#FF9800",
        "combo": "#4CAF50",
    }

    for cond in CONDITION_ORDER:
        if cond not in summaries or "collusion_index_mean" not in summaries[cond]:
            continue
        s = summaries[cond]
        conditions.append(CONDITION_LABELS.get(cond, cond))
        ci_means.append(s["collusion_index_mean"])
        ci_sems.append(s.get("collusion_index_sem", 0))

        if cond.startswith("base"):
            colors_list.append(color_map["base"])
        elif cond.startswith("deter") and "oversight" not in cond:
            colors_list.append(color_map["deter"])
        elif "oversight" in cond or "overseer" in cond:
            colors_list.append(color_map["oversight"])
        else:
            colors_list.append(color_map["combo"])

    if not conditions:
        print("No data to plot", file=sys.stderr)
        return

    x = np.arange(len(conditions))
    bars = ax.bar(x, ci_means, yerr=ci_sems, capsize=4, color=colors_list, edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(conditions, fontsize=8)
    ax.set_ylabel("Collusion Index (0 = competitive, 1 = cartel)", fontsize=11)
    ax.set_title("The Deterrence Curve: Prompt-Based vs. LLM Oversight Anti-Collusion Interventions", fontsize=13, fontweight="bold")
    ax.axhline(y=0, color="green", linestyle="--", alpha=0.5, label="Competitive Eq. ($90)")
    ax.axhline(y=1, color="red", linestyle="--", alpha=0.5, label="Full Cartel ($100)")
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(-0.2, 1.3)
    ax.grid(axis="y", alpha=0.3)

    # Add cost annotations
    for i, cond in enumerate([c for c in CONDITION_ORDER if c in summaries and "collusion_index_mean" in summaries[c]]):
        cost = CONDITION_COSTS.get(cond, 0)
        cost_label = "Free" if cost == 0 else f"~${cost:.0f}/run"
        ax.annotate(cost_label, (i, ci_means[i] + ci_sems[i] + 0.03), ha="center", fontsize=7, color="gray")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Plot saved to {output_path}")
    plt.close()

    # ── Figure 2: Deterrence levels only (the curve itself) ──
    deterrence_conds = [c for c in CONDITION_ORDER if c.startswith("deter-") and "oversight" not in c]
    deter_labels = ["Vague", "Moderate", "Severe", "Probabilistic", "Demonstrated", "Transparency"]
    deter_data = []

    for cond in deterrence_conds:
        if cond in summaries and "collusion_index_mean" in summaries[cond]:
            deter_data.append(summaries[cond])

    if len(deter_data) >= 2:
        fig2, ax2 = plt.subplots(figsize=(10, 6))

        d_ci = [d["collusion_index_mean"] for d in deter_data]
        d_sem = [d.get("collusion_index_sem", 0) for d in deter_data]
        d_labels = deter_labels[:len(deter_data)]

        # Add baselines as horizontal lines
        if "base-comms" in summaries:
            ax2.axhline(y=summaries["base-comms"].get("collusion_index_mean", 0),
                       color="red", linestyle="--", alpha=0.7, label="No Restriction (comms only)")
        if "oversight-comms" in summaries:
            ax2.axhline(y=summaries["oversight-comms"].get("collusion_index_mean", 0),
                       color="orange", linestyle="--", alpha=0.7, label="LLM Oversight ($1/run)")
        if "base-no-comms" in summaries:
            ax2.axhline(y=summaries["base-no-comms"].get("collusion_index_mean", 0),
                       color="green", linestyle="--", alpha=0.7, label="No Comms (baseline)")

        ax2.errorbar(range(len(d_ci)), d_ci, yerr=d_sem, marker="o", markersize=8,
                    linewidth=2, color="#2196F3", capsize=5, label="Deterrence (free)")
        ax2.set_xticks(range(len(d_labels)))
        ax2.set_xticklabels(d_labels, fontsize=10)
        ax2.set_ylabel("Collusion Index", fontsize=11)
        ax2.set_xlabel("Deterrence Severity Level", fontsize=11)
        ax2.set_title("The Deterrence Curve: Can Free Prompt Warnings Match Expensive LLM Oversight?",
                      fontsize=12, fontweight="bold")
        ax2.legend(fontsize=9)
        ax2.grid(axis="y", alpha=0.3)

        curve_path = output_path.with_name("deterrence_curve_only.png")
        plt.tight_layout()
        plt.savefig(curve_path, dpi=150, bbox_inches="tight")
        print(f"Deterrence curve plot saved to {curve_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="Analyze deterrence experiment results")
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

    # Compute summaries
    summaries = {}
    for tag, metrics_list in grouped.items():
        summaries[tag] = compute_summary(metrics_list)

    # Output
    print_table(grouped, summaries)
    write_csv(summaries, output_dir / "deterrence_results.csv")
    plot_deterrence_curve(summaries, output_dir / "deterrence_comparison.png")

    # Print key findings
    print("\n── Key Findings ──")
    if "base-comms" in summaries and "base-no-comms" in summaries:
        delta = summaries["base-comms"].get("collusion_index_mean", 0) - summaries["base-no-comms"].get("collusion_index_mean", 0)
        print(f"  Communication premium: {delta:+.3f} CI (comms vs no-comms)")

    if "base-comms" in summaries:
        baseline_ci = summaries["base-comms"]["collusion_index_mean"]
        print(f"  Baseline with comms: CI = {baseline_ci:.3f}")

        best_free = None
        best_free_name = None
        for cond in ["deter-vague", "deter-moderate", "deter-severe", "deter-prob", "deter-demonstrated", "deter-transparency"]:
            if cond in summaries and "collusion_index_mean" in summaries[cond]:
                ci = summaries[cond]["collusion_index_mean"]
                if best_free is None or ci < best_free:
                    best_free = ci
                    best_free_name = cond

        if best_free is not None:
            reduction = baseline_ci - best_free
            print(f"  Best free deterrence: {best_free_name} (CI = {best_free:.3f}, reduction = {reduction:+.3f})")

        if "oversight-comms" in summaries:
            oversight_ci = summaries["oversight-comms"]["collusion_index_mean"]
            print(f"  LLM oversight: CI = {oversight_ci:.3f} (~$1/run)")
            if best_free is not None:
                if best_free <= oversight_ci:
                    print(f"  → FREE deterrence ({best_free_name}) matches or beats LLM oversight!")
                else:
                    gap = best_free - oversight_ci
                    print(f"  → LLM oversight still {gap:.3f} CI better than best free deterrence")


if __name__ == "__main__":
    main()
