#!/bin/bash
cd "$(dirname "$0")"
for a in A B C; do Rscript run_robyn_mc.R 0 $a 300 1 results/RXM_smoke.csv 2 2>&1 | tail -3; done
