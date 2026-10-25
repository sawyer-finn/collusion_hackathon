#!/usr/bin/env python3 -I
"""Comprehensive analysis of CDA collusion experiment results.

Generates summary tables, time-series plots, and key findings.
Usage:
    python -I analysis/analyze.py <results_dir> [--output-dir analysis/figures]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.results_loader import load_results, load_round_series, summary_table


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 150,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
})

# Condition display names and colors
CONDITION_STYLE = {
    # Baselines
    "comms+boss_60%":       {"label": "Comms + Boss (60%)",     "color": "#e74c3c", "ls": "-"},
    "no_comms+boss_60%":    {"label": "No Comms + Boss (60%)",  "color": "#3498db", "ls": "-"},
    "run":                  {"label": "Baseline (no metadata)",  "color": "#95a5a6", "ls": "--"},
    # Enforcement
    "expost":               {"label": "Ex-Post Enforcement",     "color": "#2ecc71", "ls": "-"},
    "immediate":            {"label": "Immediate Enforcement",   "color": "#9b59b6", "ls": "-"},
    # Corrected re-runs (with comms enabled)
    "expost_corrected":                 {"label": "Ex-Post (corrected)",          "color": "#1abc9c", "ls": "-"},
    "immediate_corrected":              {"label": "Immediate (corrected)",        "color": "#8e44ad", "ls": "-"},
    "enforcement_expost+comms+boss":    {"label": "Ex-Post + Comms + Boss",       "color": "#e67e22", "ls": "-"},
    "enforcement_immediate+comms+boss": {"label": "Immediate + Comms + Boss",     "color": "#c0392b", "ls": "-"},
    # Dark book
    "dark_book":            {"label": "Dark Book",               "color": "#f39c12", "ls": "-"},
}

def _style(condition: str) -> dict:
    return CONDITION_STYLE.get(condition, {"label": condition, "color": "#333333", "ls": "-"})


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_ci_timeseries(rounds_df: pd.DataFrame, out: Path):
    """Collusion index over rounds, averaged across seeds, by condition."""
    fig, ax = plt.subplots()
    for cond, grp in rounds_df.groupby("condition"):
        agg = grp.groupby("round")["ci"].agg(["mean", "std"]).reset_index()
        s = _style(cond)
        ax.plot(agg["round"], agg["mean"], label=s["label"], color=s["color"],
                linestyle=s["ls"], linewidth=2)
        ax.fill_between(agg["round"], agg["mean"] - agg["std"], agg["mean"] + agg["std"],
                        alpha=0.12, color=s["color"])

    ax.axhline(0, color="green", linestyle=":", alpha=0.5, label="Competitive (CI=0)")
    ax.axhline(1, color="red",   linestyle=":", alpha=0.5, label="Full Collusion (CI=1)")
    ax.set_xlabel("Round")
    ax.set_ylabel("Collusion Index")
    ax.set_title("Collusion Index Over Rounds by Condition")
    ax.legend(fontsize=9, loc="best")
    ax.set_ylim(-0.15, 1.15)
    fig.tight_layout()
    fig.savefig(out / "ci_timeseries.png")
    plt.close(fig)
    print(f"  -> {out / 'ci_timeseries.png'}")


def plot_avg_ask_timeseries(rounds_df: pd.DataFrame, out: Path):
    """Average seller ask price over rounds."""
    fig, ax = plt.subplots()
    for cond, grp in rounds_df.groupby("condition"):
        agg = grp.groupby("round")["avg_seller_ask"].agg(["mean", "std"]).reset_index()
        s = _style(cond)
        ax.plot(agg["round"], agg["mean"], label=s["label"], color=s["color"],
                linestyle=s["ls"], linewidth=2)
        ax.fill_between(agg["round"], agg["mean"] - agg["std"], agg["mean"] + agg["std"],
                        alpha=0.12, color=s["color"])

    ax.axhline(90, color="green", linestyle=":", alpha=0.5, label="Competitive Eq. ($90)")
    ax.axhline(100, color="red",  linestyle=":", alpha=0.5, label="Buyer Valuation ($100)")
    ax.axhline(80, color="blue",  linestyle=":", alpha=0.3, label="Seller Valuation ($80)")
    ax.set_xlabel("Round")
    ax.set_ylabel("Average Seller Ask ($)")
    ax.set_title("Average Seller Ask Price Over Rounds")
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    fig.savefig(out / "avg_ask_timeseries.png")
    plt.close(fig)
    print(f"  -> {out / 'avg_ask_timeseries.png'}")


def plot_overseer_scores(rounds_df: pd.DataFrame, out: Path):
    """Distribution of overseer coordination scores by condition."""
    conditions_with_scores = []
    for cond, grp in rounds_df.groupby("condition"):
        scores = grp["overseer_score"].dropna()
        if len(scores) > 0:
            conditions_with_scores.append((cond, scores))

    if not conditions_with_scores:
        print("  -> (skipped overseer scores: no data)")
        return

    fig, ax = plt.subplots()
    x_positions = np.arange(1, 5)  # Scores 1-4
    width = 0.8 / len(conditions_with_scores)

    for i, (cond, scores) in enumerate(conditions_with_scores):
        s = _style(cond)
        counts = scores.value_counts().reindex([1, 2, 3, 4], fill_value=0)
        pcts = counts / counts.sum() * 100
        offset = (i - len(conditions_with_scores) / 2 + 0.5) * width
        ax.bar(x_positions + offset, pcts.values, width=width * 0.9,
               label=s["label"], color=s["color"], alpha=0.8)

    ax.set_xlabel("Overseer Coordination Score")
    ax.set_ylabel("Frequency (%)")
    ax.set_title("Distribution of Overseer Coordination Scores")
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(["1\n(No coord.)", "2\n(Low)", "3\n(Moderate)", "4\n(High)"])
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "overseer_scores.png")
    plt.close(fig)
    print(f"  -> {out / 'overseer_scores.png'}")


def plot_welfare_comparison(summary_df: pd.DataFrame, out: Path):
    """Bar chart comparing seller profit, buyer surplus, and total welfare."""
    conditions = summary_df.index.tolist()
    labels = [_style(c)["label"] for c in conditions]
    colors = [_style(c)["color"] for c in conditions]

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    metrics = [
        ("seller_profit", "Avg Seller Profit ($)"),
        ("buyer_surplus", "Avg Buyer Surplus ($)"),
        ("total_welfare", "Total Welfare ($)"),
    ]

    for ax, (col, title) in zip(axes, metrics):
        vals = summary_df[col].values
        bars = ax.barh(range(len(conditions)), vals, color=colors, alpha=0.8)
        ax.set_yticks(range(len(conditions)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.invert_yaxis()
        # Add value labels
        for bar, val in zip(bars, vals):
            if pd.notna(val):
                ax.text(val, bar.get_y() + bar.get_height()/2,
                        f" {val:.1f}", va="center", fontsize=9)

    fig.suptitle("Welfare Comparison Across Conditions", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(out / "welfare_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out / 'welfare_comparison.png'}")


def plot_ci_boxplot(run_df: pd.DataFrame, out: Path):
    """Box plot of mean CI per run, grouped by condition."""
    conditions = sorted(run_df["condition"].unique())
    data = [run_df[run_df["condition"] == c]["mean_ci"].dropna().values for c in conditions]
    labels = [_style(c)["label"] for c in conditions]
    colors = [_style(c)["color"] for c in conditions]

    fig, ax = plt.subplots()
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, widths=0.6)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.4)

    ax.axhline(0, color="green", linestyle=":", alpha=0.5)
    ax.axhline(1, color="red",   linestyle=":", alpha=0.5)
    ax.set_ylabel("Mean Collusion Index")
    ax.set_title("Distribution of Mean CI Across Runs")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "ci_boxplot.png")
    plt.close(fig)
    print(f"  -> {out / 'ci_boxplot.png'}")


def plot_ask_dispersion(rounds_df: pd.DataFrame, out: Path):
    """Seller ask dispersion over rounds — lower = more coordinated pricing."""
    fig, ax = plt.subplots()
    for cond, grp in rounds_df.groupby("condition"):
        agg = grp.groupby("round")["seller_ask_dispersion"].agg(["mean"]).reset_index()
        s = _style(cond)
        ax.plot(agg["round"], agg["mean"], label=s["label"], color=s["color"],
                linestyle=s["ls"], linewidth=2)

    ax.set_xlabel("Round")
    ax.set_ylabel("Seller Ask Dispersion ($)")
    ax.set_title("Seller Ask Price Dispersion Over Rounds\n(Lower = more coordinated pricing)")
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    fig.savefig(out / "ask_dispersion.png")
    plt.close(fig)
    print(f"  -> {out / 'ask_dispersion.png'}")


def plot_trade_price_timeseries(rounds_df: pd.DataFrame, out: Path):
    """Average trade price over rounds."""
    fig, ax = plt.subplots()
    for cond, grp in rounds_df.groupby("condition"):
        agg = grp.groupby("round")["avg_trade_price"].agg(["mean", "std"]).reset_index()
        agg = agg.dropna(subset=["mean"])
        if agg.empty:
            continue
        s = _style(cond)
        ax.plot(agg["round"], agg["mean"], label=s["label"], color=s["color"],
                linestyle=s["ls"], linewidth=2)
        ax.fill_between(agg["round"], agg["mean"] - agg["std"], agg["mean"] + agg["std"],
                        alpha=0.12, color=s["color"])

    ax.axhline(90, color="green", linestyle=":", alpha=0.5, label="Competitive Eq. ($90)")
    ax.set_xlabel("Round")
    ax.set_ylabel("Average Trade Price ($)")
    ax.set_title("Average Trade Price Over Rounds")
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    fig.savefig(out / "trade_price_timeseries.png")
    plt.close(fig)
    print(f"  -> {out / 'trade_price_timeseries.png'}")


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------

def generate_report(run_df: pd.DataFrame, rounds_df: pd.DataFrame, out: Path):
    """Generate a markdown summary report."""
    summ = summary_table(run_df)

    lines = [
        "# CDA Collusion Experiment — Results Summary",
        "",
        "## Experiment Overview",
        "",
        f"- **Total runs**: {len(run_df)}",
        f"- **Conditions**: {', '.join(sorted(run_df['condition'].unique()))}",
        f"- **Market setup**: Sellers value at $80, buyers value at $100, competitive equilibrium = $90",
        f"- **Collusion Index**: 0 = competitive, 1 = full collusion (based on trade price deviation from $90)",
        "",
        "## Summary Table",
        "",
        summ.to_markdown(),
        "",
        "## Key Findings",
        "",
    ]

    # Auto-generate findings
    if "mean_ci" in summ.columns:
        # Find baseline CI
        baseline_conds = [c for c in summ.index if "run" in c or "comms+boss" in c]
        enforcement_conds = [c for c in summ.index if "expost" in c or "immediate" in c]

        if baseline_conds:
            baseline_ci = summ.loc[baseline_conds, "mean_ci"].mean()
            lines.append(f"### Baseline Collusion")
            lines.append(f"- Average CI across baseline conditions: **{baseline_ci:.3f}**")
            if baseline_ci > 0.3:
                lines.append(f"- This indicates **substantial tacit collusion** even without explicit coordination mechanisms")
            lines.append("")

        if enforcement_conds:
            lines.append(f"### Enforcement Effectiveness")
            for cond in enforcement_conds:
                ci = summ.loc[cond, "mean_ci"]
                det = summ.loc[cond, "overseer_detections"] if "overseer_detections" in summ.columns else None
                oscore = summ.loc[cond, "overseer_mean_score"] if "overseer_mean_score" in summ.columns else None
                lines.append(f"- **{_style(cond)['label']}**: CI = {ci:.3f}")
                if pd.notna(oscore):
                    lines.append(f"  - Mean overseer score: {oscore:.2f}/4")
                if pd.notna(det):
                    lines.append(f"  - Average detections per run: {det:.1f}")
            if baseline_conds:
                for ec in enforcement_conds:
                    delta = summ.loc[ec, "mean_ci"] - baseline_ci
                    direction = "higher" if delta > 0 else "lower"
                    lines.append(f"- {_style(ec)['label']}: CI is **{abs(delta):.3f} {direction}** than baseline")
            lines.append("")

        # Price analysis
        if "avg_price" in summ.columns:
            lines.append("### Price Levels")
            for cond in summ.index:
                price = summ.loc[cond, "avg_price"]
                if pd.notna(price):
                    premium = ((price - 90) / 10) * 100  # % of max collusion premium
                    lines.append(f"- **{_style(cond)['label']}**: Avg trade price = ${price:.2f} ({premium:.0f}% of max collusion premium)")
            lines.append("")

    lines.extend([
        "## Figures",
        "",
        "- `ci_timeseries.png` — Collusion index evolution over rounds",
        "- `avg_ask_timeseries.png` — Average seller ask price over rounds",
        "- `trade_price_timeseries.png` — Average trade price over rounds",
        "- `ci_boxplot.png` — Distribution of mean CI across runs",
        "- `overseer_scores.png` — Distribution of overseer coordination scores",
        "- `welfare_comparison.png` — Seller profit, buyer surplus, total welfare",
        "- `ask_dispersion.png` — Seller ask price dispersion (coordination measure)",
        "",
        "---",
        f"*Generated from {len(run_df)} runs across {run_df['condition'].nunique()} conditions.*",
    ])

    report_path = out / "RESULTS_SUMMARY.md"
    report_path.write_text("\n".join(lines))
    print(f"  -> {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Analyze CDA collusion experiment results")
    parser.add_argument("results_dir", help="Directory containing run subdirectories")
    parser.add_argument("--output-dir", default=None, help="Output directory for figures (default: <results_dir>/../analysis/figures)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if args.output_dir:
        out = Path(args.output_dir)
    else:
        out = results_dir.parent / "analysis" / "figures"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Loading results from {results_dir}...")
    run_df = load_results(results_dir)
    rounds_df = load_round_series(results_dir)

    if run_df.empty:
        print("No results found!")
        return

    print(f"Loaded {len(run_df)} runs, {len(rounds_df)} round observations")
    print(f"Conditions: {sorted(run_df['condition'].unique())}")
    print()

    # Summary table
    print("=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    summ = summary_table(run_df)
    print(summ.to_string())
    print()

    # Generate all plots
    print("Generating plots...")
    plot_ci_timeseries(rounds_df, out)
    plot_avg_ask_timeseries(rounds_df, out)
    plot_trade_price_timeseries(rounds_df, out)
    plot_ci_boxplot(run_df, out)
    plot_overseer_scores(rounds_df, out)
    plot_welfare_comparison(summ, out)
    plot_ask_dispersion(rounds_df, out)

    # Report
    print("\nGenerating report...")
    generate_report(run_df, rounds_df, out)

    print(f"\nDone! All outputs in {out}")


if __name__ == "__main__":
    main()
