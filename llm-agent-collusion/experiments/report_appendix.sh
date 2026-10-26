#!/bin/bash
# Regenerates results/report_appendix_tables.md (per-seed tables, report layout).
cd "$(dirname "$0")/.."
t() { if [[ "$1" == --seeds=* ]]; then python3 -I experiments/report_stats.py "$1" --table "${@:2}"; else python3 -I experiments/report_stats.py --table "$@"; fi; }
{
t control41 "Table A1. Control (control41): gpt-4.1 sellers, gpt-4.1-mini buyers, messaging + pressure, 5x5" 75
t c1_nomsg "Table A2. No messaging (c1_nomsg), 5x5" 75
t c2_msgcap "Table A3. Message cap, 5 characters (c2_msgcap), 5x5" 75
t c3_overseer "Table A4. Overseer + gag (c3_overseer), 5x5" 75
t c5_sellertemp "Table A5. Seller temperature 1.2 (c5_sellertemp), 5x5" 75
t c8_random "Table A6. Random entrant x1 (c8_random), 5x5" 75
t c9_noregret1 "Table A7. No-regret entrant x1 (c9_noregret1), 5x5" 75
t c8b_random2 "Table A8. Random entrant x2 (c8b_random2), 5x5" 75
t c11_mixed "Table A9. No-regret + random entrant (c11_mixed), 5x5" 75
t c10_noregret2 "Table A10. No-regret entrant x2 (c10_noregret2), 5x5" 75
t control41_3s "Table A11. 3-LLM-seller control, no entrants, 3x5 (control41_3s)" 45
t q7_control "Table A12. Control, 7x7 (q7_control)" 105
t q7_noregret1 "Table A13. No-regret entrant x1, 7x7 (q7_noregret1)" 105
t q7_noregret2 "Table A14. No-regret entrant x2, 7x7 (q7_noregret2)" 105
t q7_noregret3 "Table A15. No-regret entrant x3, 7x7 (q7_noregret3)" 105
t q9_control "Table A16. Control, 9x9 (q9_control)" 135
t q9_noregret1 "Table A17. No-regret entrant x1, 9x9 (q9_noregret1)" 135
t q9_noregret2 "Table A18. No-regret entrant x2, 9x9 (q9_noregret2)" 135
t q9_noregret3 "Table A18b. No-regret entrant x3, 9x9 (q9_noregret3)" 135
t q15_control "Table A18c. Control, 15x15 (q15_control)" 225
t --seeds=0,1,2,3,4 q15_noregret1 "Table A18d. No-regret entrant x1, 15x15 (q15_noregret1)" 225
t q15_noregret2 "Table A18e. No-regret entrant x2, 15x15 (q15_noregret2)" 225
t q15_noregret3 "Table A18f. No-regret entrant x3, 15x15 (q15_noregret3)" 225
t q15_noregret4 "Table A18g. No-regret entrant x4, 15x15 (q15_noregret4)" 225
t q21_control "Table A18h. Control gate, 21x21, 1 seed (q21_control)" 315
t anchor_c0_control "Table A19. Control with gpt-4.1 buyers, 5x5 (anchor_c0_control)" 75
t anchor_c10_noregret2 "Table A20. No-regret entrant x2 with gpt-4.1 buyers, 5x5 (anchor_c10_noregret2)" 75
t anchor_c1_nomsg "Table A21. No messaging with gpt-4.1 buyers, 5x5 (anchor_c1_nomsg)" 75
t g4o_control "Table A22. Control with gpt-4o sellers, 5x5 (g4o_control)" 75
t g4o_noregret2 "Table A23. No-regret entrant x2 with gpt-4o sellers, 5x5, stopped after 8 seeds (g4o_noregret2)" 75
t s55_control "Table A24. Control gate with Claude Sonnet 5.5 sellers, 5x5, 1 seed (s55_control)" 75
t ds31_control "Table A25. Control gate with DeepSeek V3.1 sellers, 5x5, 1 seed (ds31_control)" 75
} > results/report_appendix_tables.md
# Number tables sequentially and fix singular "seed".
python3 -I - <<'PY'
import re
p = "results/report_appendix_tables.md"
s = open(p).read()
n = iter(range(1, 1000))
s = re.sub(r"Table A\w+\.", lambda m: f"Table A{next(n)}.", s)
open(p, "w").write(s.replace(" - 1 seeds,", " - 1 seed,"))
PY
