"""Interactive analysis of CDA collusion experiment results.

Open in VSCode → run cells with Shift+Enter (needs Python/Jupyter extension).
"""

# %% [markdown]
# # CDA Collusion Experiment Analysis

# %% Setup
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.results_loader import load_results, load_round_series, summary_table

plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 120,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 11,
})

CONDITION_STYLE = {
    "comms+boss_60%":       {"label": "Comms + Boss (60%)",     "color": "#e74c3c", "ls": "-"},
    "no_comms+boss_60%":    {"label": "No Comms + Boss (60%)",  "color": "#3498db", "ls": "-"},
    "run":                  {"label": "Baseline (no metadata)",  "color": "#95a5a6", "ls": "--"},
    "expost":               {"label": "Ex-Post Enforcement",     "color": "#2ecc71", "ls": "-"},
    "immediate":            {"label": "Immediate Enforcement",   "color": "#9b59b6", "ls": "-"},
    "expost_corrected":                 {"label": "Ex-Post (corrected)",          "color": "#1abc9c", "ls": "-"},
    "immediate_corrected":              {"label": "Immediate (corrected)",        "color": "#8e44ad", "ls": "-"},
    "enforcement_expost+comms+boss":    {"label": "Ex-Post + Comms + Boss",       "color": "#e67e22", "ls": "-"},
    "enforcement_immediate+comms+boss": {"label": "Immediate + Comms + Boss",     "color": "#c0392b", "ls": "-"},
    # Threshold 3 (stricter overseer)
    "comms+boss+thresh3":                        {"label": "Control (thresh 3)",              "color": "#7f8c8d", "ls": "--"},
    "enforcement_expost+comms+boss+thresh3":     {"label": "Ex-Post + Comms (thresh 3)",      "color": "#16a085", "ls": "-."},
    "enforcement_immediate+comms+boss+thresh3":  {"label": "Immediate + Comms (thresh 3)",    "color": "#d35400", "ls": "-."},
    # Dark book
    "dark_book":            {"label": "Dark Book",               "color": "#f39c12", "ls": "-"},
    "dark_book_comms":      {"label": "Dark Book + Comms",       "color": "#f1c40f", "ls": "-"},
    "dark_book_no_comms":   {"label": "Dark Book (no comms)",    "color": "#d4ac0d", "ls": "-"},
    "dark_book_partial_boss": {"label": "Dark Book (partial boss)", "color": "#b7950b", "ls": "--"},
}

def _style(cond):
    return CONDITION_STYLE.get(cond, {"label": cond, "color": "#333333", "ls": "-"})

# %% Load data
# ---- EDIT THIS ----
RESULTS_DIR = Path("/mnt/c/Users/tahuc/Documents/collusion_results")
# RESULTS_DIR = Path("../collusion_results")  # alternative

run_df = load_results(RESULTS_DIR)
rounds_df = load_round_series(RESULTS_DIR)
print(f"Loaded {len(run_df)} runs, {len(rounds_df)} round observations")
print(f"Conditions: {sorted(run_df['condition'].unique())}")

# %% Summary table
summary_table(run_df)

# %% Collusion Index over rounds
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
ax.set(xlabel="Round", ylabel="Collusion Index", title="Collusion Index Over Rounds")
ax.set_ylim(-0.15, 1.15)
ax.legend(fontsize=9)
fig.tight_layout()
plt.show()

# %% Average seller ask price
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
ax.set(xlabel="Round", ylabel="Average Seller Ask ($)", title="Average Seller Ask Price Over Rounds")
ax.legend(fontsize=9)
fig.tight_layout()
plt.show()

# %% Trade price over rounds
fig, ax = plt.subplots()
for cond, grp in rounds_df.groupby("condition"):
    agg = grp.groupby("round")["avg_trade_price"].agg(["mean", "std"]).reset_index().dropna(subset=["mean"])
    if agg.empty:
        continue
    s = _style(cond)
    ax.plot(agg["round"], agg["mean"], label=s["label"], color=s["color"],
            linestyle=s["ls"], linewidth=2)
    ax.fill_between(agg["round"], agg["mean"] - agg["std"], agg["mean"] + agg["std"],
                    alpha=0.12, color=s["color"])
ax.axhline(90, color="green", linestyle=":", alpha=0.5, label="Competitive Eq. ($90)")
ax.set(xlabel="Round", ylabel="Average Trade Price ($)", title="Average Trade Price Over Rounds")
ax.legend(fontsize=9)
fig.tight_layout()
plt.show()

# %% CI box plot
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
plt.show()

# %% Overseer score distribution
conditions_with_scores = []
for cond, grp in rounds_df.groupby("condition"):
    scores = grp["overseer_score"].dropna()
    if len(scores) > 0:
        conditions_with_scores.append((cond, scores))

if conditions_with_scores:
    fig, ax = plt.subplots()
    x_positions = np.arange(1, 5)
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
    plt.show()
else:
    print("No overseer score data")

# %% Welfare comparison
summ = summary_table(run_df)
conditions = summ.index.tolist()
labels = [_style(c)["label"] for c in conditions]
colors = [_style(c)["color"] for c in conditions]

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, (col, title) in zip(axes, [
    ("seller_profit", "Avg Seller Profit ($)"),
    ("buyer_surplus", "Avg Buyer Surplus ($)"),
    ("total_welfare", "Total Welfare ($)"),
]):
    vals = summ[col].values
    bars = ax.barh(range(len(conditions)), vals, color=colors, alpha=0.8)
    ax.set_yticks(range(len(conditions)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_title(title, fontsize=11)
    ax.invert_yaxis()
    for bar, val in zip(bars, vals):
        if pd.notna(val):
            ax.text(val, bar.get_y() + bar.get_height()/2, f" {val:.1f}", va="center", fontsize=9)
fig.suptitle("Welfare Comparison Across Conditions", fontsize=13, y=1.02)
fig.tight_layout()
plt.show()

# %% Ask dispersion
fig, ax = plt.subplots()
for cond, grp in rounds_df.groupby("condition"):
    agg = grp.groupby("round")["seller_ask_dispersion"].agg(["mean"]).reset_index()
    s = _style(cond)
    ax.plot(agg["round"], agg["mean"], label=s["label"], color=s["color"],
            linestyle=s["ls"], linewidth=2)
ax.set(xlabel="Round", ylabel="Seller Ask Dispersion ($)",
       title="Seller Ask Price Dispersion Over Rounds\n(Lower = more coordinated pricing)")
ax.legend(fontsize=9)
fig.tight_layout()
plt.show()

# %% [markdown]
# ## Custom exploration
# `run_df` has one row per run, `rounds_df` one row per round per run.

# %% CI by condition stats
run_df.groupby("condition")["mean_ci"].describe()

# %% Overseer score vs CI scatter
has_scores = run_df.dropna(subset=["overseer_mean_score"])
if not has_scores.empty:
    fig, ax = plt.subplots()
    for cond, grp in has_scores.groupby("condition"):
        s = _style(cond)
        ax.scatter(grp["overseer_mean_score"], grp["mean_ci"],
                   label=s["label"], color=s["color"], s=60, alpha=0.8)
    ax.set(xlabel="Mean Overseer Score", ylabel="Mean Collusion Index",
           title="Overseer Score vs Collusion Index")
    ax.legend(fontsize=9)
    plt.show()
