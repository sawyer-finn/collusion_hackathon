"""Load CDA experiment results into tidy DataFrames for analysis.

Usage:
    from analysis.results_loader import load_results, load_round_series

    # Summary DataFrame: one row per run
    df = load_results("results/")          # or any directory of run folders
    df = load_results("results/", tag_filter="baseline")  # filter by tag substring

    # Round-level DataFrame: one row per (run, round)
    rounds = load_round_series("results/")

Both functions auto-detect the condition from the experiment_metadata.json
(if present) or fall back to parsing the directory name.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_seed_from_dirname(dirname: str) -> Optional[int]:
    """Extract seed number from directory name like '20261024_143401_run-seed0'."""
    m = re.search(r"seed(\d+)", dirname)
    return int(m.group(1)) if m else None


def _parse_tag_from_dirname(dirname: str) -> str:
    """Extract tag/condition from directory name.
    '20261024_143401_run-seed0' -> 'run'
    '20261025_114153_expost-seed0' -> 'expost'
    """
    # Strip the timestamp prefix (YYYYMMDD_HHMMSS_)
    m = re.match(r"\d{8}_\d{6}_(.*)", dirname)
    if not m:
        return dirname
    rest = m.group(1)
    # Strip -seedN suffix
    rest = re.sub(r"-seed\d+$", "", rest)
    return rest


def _infer_condition(meta: Optional[dict], dirname: str) -> str:
    """Build a human-readable condition label from metadata or dirname."""
    if meta is None:
        return _parse_tag_from_dirname(dirname)

    ac = meta.get("auction_config", {})
    tag = ac.get("tag", "")

    # Build from params
    parts = []

    # Oversight threat
    ot = ac.get("oversight_threat")
    if ot:
        parts.append(f"enforcement_{ot}")

    # Dark book
    if ac.get("dark_book"):
        parts.append("dark_book")

    # Comms
    if ac.get("seller_comms_enabled"):
        parts.append("comms")
    else:
        parts.append("no_comms")

    # Boss pressure
    if ac.get("boss_pressure"):
        frac = ac.get("boss_pressure_fraction", 1.0)
        if frac < 1.0:
            parts.append(f"boss_{frac:.0%}")
        else:
            parts.append("boss")

    # Deterrence
    det = ac.get("deterrence_level")
    if det:
        parts.append(f"deterrence_{det}")

    # Overseer threshold (if non-default)
    thresh = ac.get("overseer_threshold", 4)
    if thresh != 4:
        parts.append(f"thresh{thresh}")

    if not parts:
        parts.append("baseline")

    return "+".join(parts)


# ---------------------------------------------------------------------------
# Main loaders
# ---------------------------------------------------------------------------

def load_results(
    results_dir: str | Path,
    tag_filter: Optional[str] = None,
    condition_map: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Load all experiment results into a summary DataFrame (one row per run).

    Args:
        results_dir: Directory containing run subdirectories.
        tag_filter: If set, only include runs whose directory name contains this substring.
        condition_map: Optional dict mapping directory-name tags to condition labels,
            e.g. {"run": "baseline", "expost": "enforcement_expost"}.
            Overrides auto-detection.

    Returns:
        DataFrame with columns:
            - run_dir, seed, condition, tag
            - mean_ci, std_ci, median_ci (collusion index stats)
            - avg_price, combined_seller_profit, combined_buyer_surplus
            - total_welfare, num_trades, trade_frequency
            - avg_seller_ask_dispersion, hhi_profit, hhi_volume
            - collusion_auc, average_pcm
            - overseer_mean_score, overseer_detections (if overseer was active)
            - seller_comms_enabled, boss_pressure, dark_book, oversight_threat
    """
    results_dir = Path(results_dir)
    rows = []

    for run_path in sorted(results_dir.iterdir()):
        if not run_path.is_dir():
            continue

        metrics_file = run_path / "collusion_metrics.json"
        if not metrics_file.exists():
            continue

        dirname = run_path.name
        if tag_filter and tag_filter not in dirname:
            continue

        with open(metrics_file) as f:
            metrics = json.load(f)

        # Load metadata if available
        meta_file = run_path / "experiment_metadata.json"
        meta = None
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)

        ac = meta.get("auction_config", {}) if meta else {}

        # Determine condition label
        if condition_map:
            raw_tag = _parse_tag_from_dirname(dirname)
            condition = condition_map.get(raw_tag, raw_tag)
        else:
            condition = _infer_condition(meta, dirname)

        # Collusion indices
        ci = [x for x in metrics.get("collusion_indices", []) if x is not None]
        ci_asks = [x for x in metrics.get("collusion_indices_avg_seller_asks", []) if x is not None]

        # Overseer scores
        overseer_scores = metrics.get("overseer_coordination_score", [])
        valid_scores = [s for s in overseer_scores if s is not None]

        row = {
            # Identifiers
            "run_dir": dirname,
            "seed": _parse_seed_from_dirname(dirname),
            "condition": condition,
            "tag": _parse_tag_from_dirname(dirname),

            # Collusion metrics
            "mean_ci": np.mean(ci) if ci else None,
            "std_ci": np.std(ci) if ci else None,
            "median_ci": np.median(ci) if ci else None,
            "mean_ci_asks": np.mean(ci_asks) if ci_asks else None,
            "collusion_auc": metrics.get("collusion_auc"),

            # Price metrics
            "avg_price": metrics.get("avg_trade_price_overall"),
            "average_pcm": metrics.get("average_pcm"),

            # Surplus / profit
            "combined_seller_profit": metrics.get("combined_seller_profits"),
            "combined_buyer_surplus": metrics.get("combined_buyer_surplus"),
            "total_welfare": metrics.get("total_welfare"),

            # Market structure
            "num_trades": metrics.get("num_trades"),
            "trade_frequency": metrics.get("trade_frequency"),
            "avg_seller_ask_dispersion": metrics.get("avg_seller_ask_dispersion"),
            "hhi_profit": metrics.get("hhi_profit"),
            "hhi_volume": metrics.get("hhi_volume"),
            "gini_coefficient_profit": metrics.get("gini_coefficient_profit"),

            # Overseer
            "overseer_mean_score": np.mean(valid_scores) if valid_scores else None,
            "overseer_detections": sum(1 for s in valid_scores if s >= 4) if valid_scores else None,
            "overseer_rounds_scored": len(valid_scores) if valid_scores else 0,

            # Experiment config (from metadata if available)
            "seller_comms_enabled": ac.get("seller_comms_enabled"),
            "boss_pressure": ac.get("boss_pressure"),
            "dark_book": ac.get("dark_book"),
            "oversight_threat": ac.get("oversight_threat"),
            "overseer_threshold": ac.get("overseer_threshold"),
            "seller_prompt_template": ac.get("seller_prompt_template"),
            "num_rounds": ac.get("rounds"),
            "num_sellers": len(ac.get("seller_valuations", [])) or None,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["condition", "seed"]).reset_index(drop=True)
    return df


def load_round_series(
    results_dir: str | Path,
    tag_filter: Optional[str] = None,
    condition_map: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Load round-level time series data (one row per run x round).

    Returns DataFrame with columns:
        - run_dir, seed, condition, round
        - ci (collusion index), ci_asks
        - avg_seller_ask, avg_buyer_bid, avg_trade_price
        - seller_profit, buyer_surplus
        - seller_ask_dispersion, buyer_bid_dispersion
        - overseer_score, overseer_coordination, overseer_type
    """
    results_dir = Path(results_dir)
    rows = []

    for run_path in sorted(results_dir.iterdir()):
        if not run_path.is_dir():
            continue

        metrics_file = run_path / "collusion_metrics.json"
        if not metrics_file.exists():
            continue

        dirname = run_path.name
        if tag_filter and tag_filter not in dirname:
            continue

        with open(metrics_file) as f:
            metrics = json.load(f)

        meta_file = run_path / "experiment_metadata.json"
        meta = None
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)

        if condition_map:
            raw_tag = _parse_tag_from_dirname(dirname)
            condition = condition_map.get(raw_tag, raw_tag)
        else:
            condition = _infer_condition(meta, dirname)

        seed = _parse_seed_from_dirname(dirname)

        # All per-round lists
        ci = metrics.get("collusion_indices", [])
        ci_asks = metrics.get("collusion_indices_avg_seller_asks", [])
        avg_asks = metrics.get("avg_seller_asks_by_round", [])
        avg_bids = metrics.get("avg_buyer_bids_by_round", [])
        avg_prices = metrics.get("avg_trade_prices_by_round", [])
        seller_profit = metrics.get("avg_seller_profit_per_round", [])
        buyer_surplus = metrics.get("avg_buyer_surplus_per_round", [])
        ask_disp = metrics.get("seller_ask_dispersions", [])
        bid_disp = metrics.get("buyer_bid_dispersions", [])
        overseer_scores = metrics.get("overseer_coordination_score", [])
        overseer_coord = metrics.get("overseer_coordination", [])
        overseer_type = metrics.get("overseer_type", [])

        n_rounds = max(len(ci), len(avg_asks), len(avg_bids), 0)
        for r in range(n_rounds):
            row = {
                "run_dir": dirname,
                "seed": seed,
                "condition": condition,
                "round": r + 1,
                "ci": ci[r] if r < len(ci) else None,
                "ci_asks": ci_asks[r] if r < len(ci_asks) else None,
                "avg_seller_ask": avg_asks[r] if r < len(avg_asks) else None,
                "avg_buyer_bid": avg_bids[r] if r < len(avg_bids) else None,
                "avg_trade_price": avg_prices[r] if r < len(avg_prices) else None,
                "seller_profit": seller_profit[r] if r < len(seller_profit) else None,
                "buyer_surplus": buyer_surplus[r] if r < len(buyer_surplus) else None,
                "seller_ask_dispersion": ask_disp[r] if r < len(ask_disp) else None,
                "buyer_bid_dispersion": bid_disp[r] if r < len(bid_disp) else None,
                "overseer_score": overseer_scores[r] if r < len(overseer_scores) else None,
                "overseer_coordination": overseer_coord[r] if r < len(overseer_coord) else None,
                "overseer_type": overseer_type[r] if r < len(overseer_type) else None,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["condition", "seed", "round"]).reset_index(drop=True)
    return df


def summary_table(df: pd.DataFrame, group_col: str = "condition") -> pd.DataFrame:
    """Aggregate a run-level DataFrame into a condition-level summary table.

    Returns one row per condition with mean +/- std for key metrics.
    """
    agg = df.groupby(group_col).agg(
        n_runs=("seed", "count"),
        mean_ci=("mean_ci", "mean"),
        std_ci=("mean_ci", "std"),
        avg_price=("avg_price", "mean"),
        seller_profit=("combined_seller_profit", "mean"),
        buyer_surplus=("combined_buyer_surplus", "mean"),
        total_welfare=("total_welfare", "mean"),
        num_trades=("num_trades", "mean"),
        avg_pcm=("average_pcm", "mean"),
        ask_dispersion=("avg_seller_ask_dispersion", "mean"),
        overseer_mean_score=("overseer_mean_score", "mean"),
        overseer_detections=("overseer_detections", "mean"),
    ).round(3)
    return agg


if __name__ == "__main__":
    import sys
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    df = load_results(results_dir)
    print(f"Loaded {len(df)} runs from {results_dir}")
    print()
    if not df.empty:
        print(summary_table(df).to_string())
