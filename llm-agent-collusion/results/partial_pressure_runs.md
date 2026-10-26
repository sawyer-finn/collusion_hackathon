# Partial-pressure runs (T.H.)

Run on 2026-10-24 with the original untagged name `run-seedN`; renamed here by condition.
Setup: 5 gpt-4.1 sellers, 5 gpt-4.1-mini buyers, 15 rounds, `--boss_pressure --boss_pressure_fraction 0.6` (3 of 5 sellers get the management warning).

| Folder prefix | Condition | Flags |
|---|---|---|
| partial3of5_shared | shared seller chat | `--seller_comms_enabled` |
| partial3of5_split | chat split by pressure group | `--seller_comms_enabled --split_comms` |
| partial3of5_nomsg | no seller messaging | (comms disabled) |

Each folder holds experiment_metadata.json, collusion_metrics.json and unified.log (per-agent transcripts stayed on the original machine).
Results are in Table G1 of the report, paired with control41 seeds 0-4.
