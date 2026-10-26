#!/bin/bash
# Regenerates every number in the report from the run logs in results/.
# Tables (G1-G4, Table 1, Figure inputs): experiments/report_stats.py
# Text numbers, Table G5 and Appendix B: experiments/report_text_numbers.py
# Early-sales regression (Section 4.4): experiments/starvation_curve.py
set -e
cd "$(dirname "$0")/.."
python3 experiments/report_stats.py control41 c5_sellertemp c2_msgcap c3_overseer c1_nomsg \
  partial3of5_shared partial3of5_split partial3of5_nomsg \
  expost_corrected immediate_corrected expost_thresh3 immediate_thresh3 expost_thresh2_boss immediate_thresh2_boss \
  expost_thresh1_boss immediate_thresh1_boss control_thresh3 \
  partial_transparency_boss dark_book_comms sequential_asks_boss dark_book_no_comms dark_book_partial_boss \
  c9_noregret1 c8_random c8b_random2 c11_mixed c10_noregret2 control41_3s > results/report_stats_5x5.txt
for s in 7 9 15; do
  python3 experiments/report_stats.py q${s}_control q${s}_noregret1 q${s}_noregret2 q${s}_noregret3 q${s}_noregret4
done > results/report_stats_scaling.txt 2>&1
{ python3 experiments/report_stats.py anchor_c0_control anchor_c10_noregret2
  python3 experiments/report_stats.py b10_control b10_noregret2
  for t in g4o_control s55_control ds31_control q21_control control; do python3 experiments/report_stats.py $t; done
} > results/report_stats_robustness.txt
python3 experiments/report_text_numbers.py > results/report_text_numbers.txt
python3 experiments/starvation_curve.py > results/starvation_curve.txt
python3 experiments/report_figures.py
bash experiments/report_appendix.sh
echo "Wrote results/report_*.txt, results/starvation_curve.txt, figures and appendix tables"
