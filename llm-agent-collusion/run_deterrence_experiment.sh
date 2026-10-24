#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Deterrence Curve Experiment — Apart Research AI Collusion Sprint
# Track 1, Q1.5: Which single restriction removes the most collusion
#                at the least cost?
#
# Conditions (all use --paper for 5 sellers, 6 ZIP buyers, 30 rounds):
#
#   BASELINES (from Agrawal et al.)
#   B1  base-no-comms     — no comms, no oversight
#   B2  base-comms        — comms enabled, no oversight
#   B3  oversight-comms   — comms + oversight (original message-only)
#
#   DETERRENCE CURVE (prompt-only, zero LLM cost)
#   D1  deter-vague       — comms + vague deterrence warning
#   D2  deter-moderate    — comms + moderate deterrence warning
#   D3  deter-severe      — comms + severe deterrence warning
#   D4  deter-prob        — comms + probabilistic deterrence
#   D5  deter-demonstrated — comms + demonstrated deterrence
#   D6  deter-transparency — comms + transparency deterrence
#
#   OVERSEER VISIBILITY VARIANTS (extended overseer, LLM cost)
#   E1  overseer-price-aware  — comms + extended overseer sees messages + prices
#   E2  overseer-price-only   — NO comms + extended overseer sees prices only
#   E3  overseer-orderbook    — comms + extended overseer sees bids/asks only
#
#   COMBINATION
#   C1  deter-severe+oversight — comms + severe deterrence + original oversight
#
# Seeds: 3 seeds per condition for statistical power within budget
# Model: gpt-4.1 (paper default) via OpenRouter
#
# Usage:
#   export OPENROUTER_API_KEY=sk-...
#   bash run_deterrence_experiment.sh [--dry-run] [--seeds "0 1 2"] [--conditions "B1 B2"]
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

# Parse optional args
DRY_RUN=false
SEEDS="0 1 2"
CONDITIONS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN=true; shift ;;
    --seeds)      SEEDS="$2"; shift 2 ;;
    --conditions) CONDITIONS="$2"; shift 2 ;;
    *)            echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Validate env
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "Error: OPENROUTER_API_KEY not set" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SIM="python $REPO_ROOT/src/continuous_double_auction/simulation.py"
COMMON="--paper --yes"  # 5 sellers, 6 ZIP buyers, 30 rounds; skip confirmation

# Build seed args
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

# ── BASELINES ──

run_B1() { run_condition "base-no-comms" ; }
run_B2() { run_condition "base-comms" --seller_comms_enabled ; }
run_B3() { run_condition "oversight-comms" --seller_comms_enabled --oversight_enabled ; }

# ── DETERRENCE CURVE (zero-cost prompt interventions) ──

run_D1() { run_condition "deter-vague" --seller_comms_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level vague ; }

run_D2() { run_condition "deter-moderate" --seller_comms_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level moderate ; }

run_D3() { run_condition "deter-severe" --seller_comms_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level severe ; }

run_D4() { run_condition "deter-prob" --seller_comms_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level probabilistic ; }

run_D5() { run_condition "deter-demonstrated" --seller_comms_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level demonstrated ; }

run_D6() { run_condition "deter-transparency" --seller_comms_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level transparency ; }

# ── OVERSEER VISIBILITY VARIANTS ──

run_E1() { run_condition "overseer-price-aware" --seller_comms_enabled --oversight_enabled \
  --overseer_prompt_template message_overseer_prompt_extended.jinja2 ; }

run_E2() { run_condition "overseer-price-only" --oversight_enabled \
  --overseer_prompt_template message_overseer_prompt_extended.jinja2 ; }

run_E3() { run_condition "overseer-orderbook" --seller_comms_enabled --oversight_enabled \
  --overseer_prompt_template message_overseer_prompt_extended.jinja2 ; }

# ── COMBINATION ──

run_C1() { run_condition "deter-severe+oversight" --seller_comms_enabled --oversight_enabled \
  --seller_prompt_template seller_prompt_cartel.jinja2 --deterrence_level severe ; }

# ── Dispatch ──

ALL_CONDITIONS="B1 B2 B3 D1 D2 D3 D4 D5 D6 E1 E2 E3 C1"
if [[ -n "$CONDITIONS" ]]; then
  RUN_LIST="$CONDITIONS"
else
  RUN_LIST="$ALL_CONDITIONS"
fi

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Deterrence Curve Experiment                       ║"
echo "║   Seeds: $SEEDS                                     "
echo "║   Conditions: $RUN_LIST                             "
echo "║   Dry run: $DRY_RUN                                 "
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Cost estimate: paper config = 330 calls/run, 3 seeds = 990 calls/condition
# gpt-4.1 via OpenRouter ≈ $0.005/call → ~$5/condition, ~$65 for all 13
n_conditions=$(echo "$RUN_LIST" | wc -w)
est_cost=$(echo "$n_conditions * 990 * 0.005" | bc)
echo "Estimated cost: ~\$$est_cost for $n_conditions conditions × $(echo $SEEDS | wc -w) seeds"
echo ""

for cond in $RUN_LIST; do
  run_"$cond"
done

echo "All conditions complete. Run analyze_deterrence.py on the results/ directory."
