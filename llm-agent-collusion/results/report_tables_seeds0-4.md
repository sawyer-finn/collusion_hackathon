### Control B (control41): gpt-4.1 sellers, mini buyers, messaging + pressure - 5 seeds, 5/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.72 | 97.20 | 38 | 106.30 |
| 1 | +0.61 | 96.14 | 55 | 212.18 |
| 2 | +0.66 | 96.58 | 27 | 92.22 |
| 3 | +0.69 | 96.97 | 49 | 148.37 |
| 4 | +0.78 | 97.60 | 16 | 38.42 |
| Mean ± SD | +0.69 ± 0.06 | 96.90 ± 0.56 | 37.0 ± 15.9 | 119.50 ± 65.03 |
| 95% bootstrap CI | [0.64, 0.74] | [96.44, 97.32] | [24.8, 49.2] | [71.17, 167.01] |

### C1 No messaging (c1_nomsg) - 5 seeds, 4/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.57 | 95.64 | 26 | 113.32 |
| 1 | +0.62 | 96.17 | 40 | 153.09 |
| 2 | +0.34 | 93.41 | 24 | 158.12 |
| 3 | +0.58 | 95.80 | 21 | 88.18 |
| 4 | +0.75 | 97.53 | 40 | 98.75 |
| Mean ± SD | +0.57 ± 0.15 | 95.71 ± 1.49 | 30.2 ± 9.1 | 122.29 ± 31.74 |
| 95% bootstrap CI | [0.44, 0.68] | [94.41, 96.81] | [23.2, 37.2] | [97.44, 147.15] |

### C2 Message cap 5 (c2_msgcap) - 5 seeds, 4/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.71 | 97.16 | 35 | 99.24 |
| 1 | +0.41 | 92.84 | 1 | 7.16 |
| 2 | +0.61 | 96.12 | 14 | 54.27 |
| 3 | +0.69 | 97.13 | 14 | 40.12 |
| 4 | +0.76 | 97.62 | 50 | 119.20 |
| Mean ± SD | +0.64 ± 0.14 | 96.18 ± 1.94 | 22.8 ± 19.5 | 64.00 ± 45.23 |
| 95% bootstrap CI | [0.52, 0.73] | [94.45, 97.34] | [8.8, 38.0] | [29.77, 99.39] |

### C3 Overseer, full (c3_overseer) - 5 seeds, 4/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.72 | 97.26 | 13 | 35.56 |
| 1 | +0.60 | 96.05 | 40 | 157.81 |
| 2 | +0.61 | 96.12 | 37 | 143.60 |
| 3 | +0.41 | 93.74 | 3 | 18.79 |
| 4 | +0.75 | 97.54 | 28 | 69.01 |
| Mean ± SD | +0.62 ± 0.13 | 96.14 ± 1.50 | 24.2 ± 15.8 | 84.95 ± 62.89 |
| 95% bootstrap CI | [0.51, 0.71] | [94.92, 97.19] | [11.8, 36.4] | [38.88, 134.37] |

### C5 Seller temperature 1.2 (c5_sellertemp) - 5 seeds, 5/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.65 | 94.25 | 1 | 5.75 |
| 1 | +0.61 | 96.08 | 36 | 141.28 |
| 2 | +0.66 | 96.37 | 19 | 68.89 |
| 3 | +0.68 | 96.79 | 29 | 93.00 |
| 4 | +0.75 | 97.57 | 27 | 65.71 |
| Mean ± SD | +0.67 ± 0.05 | 96.21 ± 1.23 | 22.4 ± 13.4 | 74.93 ± 49.08 |
| 95% bootstrap CI | [0.63, 0.72] | [95.12, 97.09] | [11.4, 31.4] | [35.19, 112.31] |

### C8 Random entrant x1 (c8_random) - 5 seeds, 4/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third), LLM sellers | Avg trade price | Trades (of 75) | Buyer surplus | Entrant profit |
|---|---|---|---|---|---|
| 0 | +0.58 | 94.48 | 34 | 187.59 | 153.74 |
| 1 | +0.26 | 92.34 | 23 | 176.27 | 96.08 |
| 2 | +0.65 | 95.17 | 40 | 193.04 | 99.31 |
| 3 | +0.61 | 95.10 | 49 | 240.09 | 153.13 |
| 4 | +0.73 | 96.08 | 43 | 168.45 | 189.18 |
| Mean ± SD | +0.56 ± 0.18 | 94.64 ± 1.41 | 37.8 ± 9.9 | 193.09 ± 27.97 | 138.29 ± 39.84 |
| 95% bootstrap CI | [0.41, 0.68] | [93.44, 95.58] | [29.6, 44.8] | [174.93, 217.92] | [108.26, 167.79] |

### C9 No-regret entrant x1 (c9_noregret1) - 5 seeds, 2/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third), LLM sellers | Avg trade price | Trades (of 75) | Buyer surplus | Entrant profit |
|---|---|---|---|---|---|
| 0 | +0.40 | 87.46 | 18 | 225.74 | 106.90 |
| 1 | +0.43 | 92.48 | 21 | 157.83 | 164.17 |
| 2 | +0.35 | 93.27 | 38 | 255.81 | 179.39 |
| 3 | +0.64 | 95.56 | 47 | 208.51 | 206.24 |
| 4 | +0.74 | 90.81 | 16 | 147.00 | 155.68 |
| Mean ± SD | +0.51 ± 0.17 | 91.92 ± 3.02 | 28.0 ± 13.7 | 198.98 ± 45.91 | 162.48 ± 36.53 |
| 95% bootstrap CI | [0.39, 0.65] | [89.47, 94.15] | [17.8, 39.4] | [163.63, 234.32] | [131.15, 189.41] |

### C8b Random entrant x2 (c8b_random2) - 5 seeds, 2/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third), LLM sellers | Avg trade price | Trades (of 75) | Buyer surplus | Entrant profit |
|---|---|---|---|---|---|
| 0 | +0.69 | 94.15 | 45 | 263.20 | 267.90 |
| 1 | +0.26 | 91.42 | 21 | 180.22 | 175.80 |
| 2 | +0.52 | 86.52 | 13 | 175.26 | 84.74 |
| 3 | +0.42 | 91.08 | 30 | 267.57 | 204.29 |
| 4 | +0.03 | 87.98 | 19 | 228.30 | 131.75 |
| Mean ± SD | +0.39 ± 0.25 | 90.23 ± 3.01 | 25.6 ± 12.4 | 222.91 ± 43.99 | 172.90 ± 69.79 |
| 95% bootstrap CI | [0.17, 0.57] | [87.79, 92.51] | [17.0, 35.6] | [187.85, 257.97] | [118.05, 227.95] |

### C11 No-regret + random entrant (c11_mixed) - 5 seeds, 1/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third), LLM sellers | Avg trade price | Trades (of 75) | Buyer surplus | Entrant profit |
|---|---|---|---|---|---|
| 0 | +0.12 | 89.07 | 32 | 349.68 | 216.68 |
| 1 | +0.38 | 85.96 | 20 | 280.80 | 110.45 |
| 2 | +0.57 | 83.08 | 11 | 186.07 | 33.93 |
| 3 | +0.01 | 89.21 | 49 | 528.81 | 177.58 |
| 4 | -0.01 | 89.41 | 45 | 476.48 | 183.70 |
| Mean ± SD | +0.21 ± 0.25 | 87.35 ± 2.77 | 31.4 ± 16.1 | 364.37 ± 140.18 | 144.47 ± 72.85 |
| 95% bootstrap CI | [0.02, 0.42] | [84.93, 89.26] | [18.8, 44.0] | [256.68, 472.05] | [79.84, 195.67] |

### C10 No-regret entrant x2 (c10_noregret2) - 5 seeds, 2/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third), LLM sellers | Avg trade price | Trades (of 75) | Buyer surplus | Entrant profit |
|---|---|---|---|---|---|
| 0 | +0.50 | 92.57 | 31 | 230.46 | 317.84 |
| 1 | -0.24 | 85.65 | 32 | 459.18 | 137.89 |
| 2 | +0.21 | 89.71 | 32 | 329.41 | 267.25 |
| 3 | -0.24 | 87.18 | 47 | 602.58 | 174.43 |
| 4 | +0.62 | 89.79 | 31 | 316.62 | 280.80 |
| Mean ± SD | +0.17 ± 0.40 | 88.98 ± 2.66 | 34.6 ± 6.9 | 387.65 ± 145.31 | 235.64 ± 75.99 |
| 95% bootstrap CI | [-0.15, 0.49] | [86.78, 90.92] | [31.2, 40.8] | [284.71, 516.54] | [173.78, 292.91] |

### 3-LLM-seller control, no entrants, 3 sellers x 5 buyers (control41_3s) - 5 seeds, 5/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 45) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.76 | 97.61 | 26 | 62.25 |
| 1 | +0.52 | 95.22 | 9 | 42.99 |
| 2 | +0.60 | 96.11 | 20 | 77.79 |
| 3 | +0.70 | 96.88 | 21 | 65.61 |
| 4 | +0.76 | 97.58 | 30 | 72.51 |
| Mean ± SD | +0.67 ± 0.11 | 96.68 ± 1.02 | 21.2 ± 7.9 | 64.23 ± 13.32 |
| 95% bootstrap CI | [0.58, 0.75] | [95.87, 97.45] | [14.6, 26.8] | [52.75, 73.24] |

### Anchor control: gpt-4.1 sellers and buyers (anchor_c0_control) - 5 seeds, 3/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.69 | 96.75 | 4 | 13.01 |
| 1 | +0.59 | 95.86 | 13 | 53.86 |
| 2 | +0.63 | 96.11 | 10 | 38.87 |
| 3 | +0.36 | 93.58 | 15 | 96.24 |
| 4 | +0.08 | 88.73 | 26 | 293.08 |
| Mean ± SD | +0.47 ± 0.25 | 94.21 ± 3.29 | 13.6 ± 8.1 | 99.01 ± 112.61 |
| 95% bootstrap CI | [0.25, 0.65] | [91.30, 96.32] | [7.6, 20.2] | [31.52, 202.87] |

### Anchor no messaging: gpt-4.1 sellers and buyers (anchor_c1_nomsg) - 5 seeds, 3/5 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | +0.67 | 96.05 | 5 | 19.74 |
| 1 | +0.46 | 94.27 | 4 | 22.92 |
| 2 | +0.49 | 94.15 | 4 | 23.40 |
| 3 | +0.67 | 96.63 | 7 | 23.60 |
| 4 | +0.73 | 97.20 | 9 | 25.21 |
| Mean ± SD | +0.61 ± 0.12 | 95.66 ± 1.38 | 5.8 ± 2.2 | 22.97 ± 2.00 |
| 95% bootstrap CI | [0.51, 0.69] | [94.58, 96.74] | [4.2, 7.6] | [21.20, 24.39] |

### Control A, failed gate: gpt-4.1-mini sellers and buyers (control) - 3 seeds, 0/3 pass gate (ask index > 0.5)

| Seed | Ask index (last third) | Avg trade price | Trades (of 75) | Buyer surplus |
|---|---|---|---|---|
| 0 | -0.60 | 84.20 | 29 | 458.26 |
| 1 | -0.55 | 84.54 | 48 | 742.29 |
| 2 | -0.70 | 83.10 | 58 | 979.96 |
| Mean ± SD | -0.62 ± 0.08 | 83.95 ± 0.75 | 45.0 ± 14.7 | 726.84 ± 261.19 |
| 95% bootstrap CI | [-0.70, -0.55] | [83.10, 84.54] | [29.0, 58.0] | [458.26, 979.96] |
