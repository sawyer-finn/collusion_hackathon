#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# New Experiments for the Collusion Paper
#
# Three experiment groups:
#
# 1. THRESHOLD SWEEP (thresholds 1 and 2)
#    - Ex-post enforcement with threshold 1 and 2
#    - Immediate enforcement with threshold 1 and 2
#    - 5 seeds each = 20 runs total
#    - No code changes needed (existing --overseer_threshold flag)
#
# 2. PARTIAL TRANSPARENCY
#    - Sellers see only the mean ask price (not individual asks)
#    - With comms enabled (to compare against full transparency + comms)
#    - 5 seeds = 5 runs
#
# 3. SEQUENTIAL ASKS
#    - Sellers see previous round's asks (not current round's)
#    - With comms enabled
#    - 5 seeds = 5 runs
#
# All conditions: 5 sellers, 5 buyers, 15 rounds, gpt-4.1, comms enabled
#
# Usage:
#   source ../compute.env   # sets OPENROUTER_API_KEY
#   bash run_new_experiments.sh [--dry-run] [--seeds "0 1 2 3 4"] [--group 1|2|3|all]
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

DRY_RUN=false
SEEDS="0 1 2 3 4"
GROUP="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=true; shift ;;
    --seeds)    SEEDS="$2"; shift 2 ;;
    --group)    GROUP="$2"; shift 2 ;;
    *)          echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "Error: OPENROUTER_API_KEY not set. Run: source ../compute.env" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SIM="uv run python $REPO_ROOT/src/continuous_double_auction/simulation.py"
COMMON="--sellers 5 --buyers 5 --rounds 15 --seller_comms_enabled -y"

SEED_ARGS=""
for s in $SEEDS; do
  SEED_ARGS="$SEED_ARGS $s"
done

run_condition() {
  local name="$1"
  shift
  local cmd="$SIM $COMMON --seeds $SEED_ARGS --tag $name $*"
  echo "━━━ $name ━━━"
  echo "  $cmd"
  if [[ "$DRY_RUN" == "false" ]]; then
    eval "$cmd"
  fi
  echo ""
}

# ══════════════════════════════════════════════════════════════════════
# GROUP 1 — THRESHOLD SWEEP (thresholds 1 and 2)
# We already have threshold 3 and 4 data. Now fill in 1 and 2.
# ══════════════════════════════════════════════════════════════════════

run_expost_t1()    { run_condition "expost_thresh1"    --oversight_threat expost    --overseer_threshold 1 ; }
run_expost_t2()    { run_condition "expost_thresh2"    --oversight_threat expost    --overseer_threshold 2 ; }
run_immediate_t1() { run_condition "immediate_thresh1" --oversight_threat immediate --overseer_threshold 1 ; }
run_immediate_t2() { run_condition "immediate_thresh2" --oversight_threat immediate --overseer_threshold 2 ; }

# ══════════════════════════════════════════════════════════════════════
# GROUP 2 — PARTIAL TRANSPARENCY
# Sellers see only the mean ask price, not individual asks.
# Tests the boundary between full transparency (collusion) and
# dark book (no collusion).
# ══════════════════════════════════════════════════════════════════════

run_partial_transparency() { run_condition "partial_transparency" --partial_transparency ; }

# ══════════════════════════════════════════════════════════════════════
# GROUP 3 — SEQUENTIAL ASKS
# Sellers see what others asked *last round* but not this round.
# Sealed-bid with delayed reveal.
# ══════════════════════════════════════════════════════════════════════

run_sequential_asks() { run_condition "sequential_asks" --sequential_asks ; }

# ── Dispatch ──

GROUP1="expost_t1 expost_t2 immediate_t1 immediate_t2"
GROUP2="partial_transparency"
GROUP3="sequential_asks"

case "$GROUP" in
  1)   RUN_LIST="$GROUP1" ;;
  2)   RUN_LIST="$GROUP2" ;;
  3)   RUN_LIST="$GROUP3" ;;
  all) RUN_LIST="$GROUP1 $GROUP2 $GROUP3" ;;
  *)   echo "Unknown --group: $GROUP (use 1, 2, 3, or all)"; exit 1 ;;
esac

n_conditions=$(echo "$RUN_LIST" | wc -w)
n_seeds=$(echo $SEEDS | wc -w)
# 5 sellers × 15 rounds = 75 LLM calls/run (sellers only; ZIP buyers are free)
# + overseer for threshold conditions ≈ 100-150 calls/run
calls_per_run=100
est_cost=$(echo "$n_conditions * $calls_per_run * $n_seeds * 0.005" | bc)

echo "╔══════════════════════════════════════════════════════╗"
echo "║   New Experiments Runner                             ║"
echo "║   Group: $GROUP                                      "
echo "║   Seeds: $SEEDS ($n_seeds)                           "
echo "║   Conditions: $n_conditions                          "
echo "║   Total runs: $((n_conditions * n_seeds))            "
echo "║   Estimated cost: ~\$$est_cost                       "
echo "║   Dry run: $DRY_RUN                                  "
echo "╚══════════════════════════════════════════════════════╝"
echo ""

for cond in $RUN_LIST; do
  run_"$cond"
done

echo "All conditions complete."
echo "Results in: results/"
