#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Collusion Restriction Experiment — Apart Research AI Collusion Sprint
# Track 1, Q1.5: Which single restriction removes the most collusion
#                at the least cost?
#
# Two principled phases:
#
# PHASE 1 — CARTEL FRAGMENTATION
# Vary what fraction of sellers receive boss pressure (CEO message).
# Tests: at what threshold does collusion collapse?
#   F0: 0/5 sellers pressured (baseline — no collusion driver)
#   F1: 1/5 sellers pressured
#   F2: 2/5 sellers pressured
#   F3: 3/5 sellers pressured
#   F4: 4/5 sellers pressured
#   F5: 5/5 sellers pressured (full collusion driver)
#
# PHASE 2 — OVERSIGHT DESIGN
# Factorial: detection method × punishment type
# Tests: what makes an overseer actually effective?
#   O0: Collusion baseline (= F5, boss pressure, comms, no oversight)
#   O1: Messages-only detection + gag order
#   O2: Messages-only detection + fines
#   O3: Price-aware detection + gag order
#   O4: Price-aware detection + fines
#   O5: Full combo: price-aware detection + gag + fines
#
# Seeds: 3 per condition for statistical power
# Model: gpt-4.1 via OpenRouter
#
# Usage:
#   source compute.env  # sets OPENROUTER_API_KEY
#   bash run_deterrence_experiment.sh [--dry-run] [--seeds "0 1 2"] [--phase 1|2|all]
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

DRY_RUN=false
SEEDS="0 1 2"
PHASE="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=true; shift ;;
    --seeds)    SEEDS="$2"; shift 2 ;;
    --phase)    PHASE="$2"; shift 2 ;;
    *)          echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "Error: OPENROUTER_API_KEY not set. Run: source compute.env" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SIM="python $REPO_ROOT/src/continuous_double_auction/simulation.py"
# Paper config: 5 sellers, 6 ZIP buyers, 30 rounds
COMMON="--paper --yes"

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
# PHASE 1 — CARTEL FRAGMENTATION
# All use: comms enabled, boss_pressure on, vary boss_pressure_fraction
# ══════════════════════════════════════════════════════════════════════

run_F0() { run_condition "frac-0of5" --seller_comms_enabled --boss_pressure --boss_pressure_fraction 0.0 ; }
run_F1() { run_condition "frac-1of5" --seller_comms_enabled --boss_pressure --boss_pressure_fraction 0.2 ; }
run_F2() { run_condition "frac-2of5" --seller_comms_enabled --boss_pressure --boss_pressure_fraction 0.4 ; }
run_F3() { run_condition "frac-3of5" --seller_comms_enabled --boss_pressure --boss_pressure_fraction 0.6 ; }
run_F4() { run_condition "frac-4of5" --seller_comms_enabled --boss_pressure --boss_pressure_fraction 0.8 ; }
run_F5() { run_condition "frac-5of5" --seller_comms_enabled --boss_pressure --boss_pressure_fraction 1.0 ; }

# ══════════════════════════════════════════════════════════════════════
# PHASE 2 — OVERSIGHT DESIGN
# All use: comms enabled, full boss_pressure (fraction=1.0)
# Factorial: detection (messages-only vs price-aware) × punishment (gag vs fine)
# ══════════════════════════════════════════════════════════════════════

# O0: Collusion baseline — same as F5 (no oversight)
run_O0() { run_condition "oversight-baseline" --seller_comms_enabled --boss_pressure ; }

# O1: Messages-only overseer + gag order (original paper design)
run_O1() { run_condition "msg-gag" --seller_comms_enabled --boss_pressure --oversight_enabled \
  --overseer_penalty gag ; }

# O2: Messages-only overseer + fines
run_O2() { run_condition "msg-fine" --seller_comms_enabled --boss_pressure --oversight_enabled \
  --overseer_penalty fine ; }

# O3: Price-aware overseer + gag order
run_O3() { run_condition "price-gag" --seller_comms_enabled --boss_pressure --oversight_enabled \
  --overseer_prompt_template message_overseer_prompt_extended.jinja2 --overseer_penalty gag ; }

# O4: Price-aware overseer + fines
run_O4() { run_condition "price-fine" --seller_comms_enabled --boss_pressure --oversight_enabled \
  --overseer_prompt_template message_overseer_prompt_extended.jinja2 --overseer_penalty fine ; }

# O5: Price-aware overseer + gag + fines (full combo)
run_O5() { run_condition "price-both" --seller_comms_enabled --boss_pressure --oversight_enabled \
  --overseer_prompt_template message_overseer_prompt_extended.jinja2 --overseer_penalty both ; }

# ── Dispatch ──

PHASE1="F0 F1 F2 F3 F4 F5"
PHASE2="O0 O1 O2 O3 O4 O5"

case "$PHASE" in
  1)   RUN_LIST="$PHASE1" ;;
  2)   RUN_LIST="$PHASE2" ;;
  all) RUN_LIST="$PHASE1 $PHASE2" ;;
  *)   echo "Unknown --phase: $PHASE (use 1, 2, or all)"; exit 1 ;;
esac

n_conditions=$(echo "$RUN_LIST" | wc -w)
n_seeds=$(echo $SEEDS | wc -w)
# paper config: 5 sellers + 6 ZIP buyers = 5 LLM calls/round × 30 rounds = 150 calls/run
# + overseer for Phase 2 oversight conditions = ~180 calls/run
calls_per_run=150
est_cost=$(echo "$n_conditions * $calls_per_run * $n_seeds * 0.005" | bc)

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Collusion Restriction Experiment                   ║"
echo "║   Phase: $PHASE                                      "
echo "║   Seeds: $SEEDS ($n_seeds)                           "
echo "║   Conditions: $n_conditions                          "
echo "║   Estimated cost: ~\$$est_cost                       "
echo "║   Dry run: $DRY_RUN                                  "
echo "╚══════════════════════════════════════════════════════╝"
echo ""

for cond in $RUN_LIST; do
  run_"$cond"
done

echo "All conditions complete. Run: python analyze_deterrence.py results/"
