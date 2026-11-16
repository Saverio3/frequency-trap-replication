#!/bin/bash
# Resumable queue for the controlled Robyn experiment (DESIGN_ROBYN_CONTROLLED.md).
# Usage: ./run_mc_queue.sh "0 1 2 3" results/RXM_full.csv 2 [iterations] [trials]
# Arms A and B for every market; arm C only for markets 0-7 (declared in the design note). Skips (market, arm) already in the output file.
cd "$(dirname "$0")"
MARKETS=${1:-"0 1 2 3"}; OUT=${2:-results/RXM_full.csv}; CORES=${3:-2}; ITERS=${4:-2000}; TRIALS=${5:-5}
for m in $MARKETS; do
  ARMS="A B"; if [ "$m" -le 7 ]; then ARMS="A B C"; fi
  for a in $ARMS; do
    if [ -f "$OUT" ] && [ "$(awk -F, -v m=$m -v a="\"$a\"" 'NR>1 && $1==m && $2==a' "$OUT" | wc -l)" -ge 2 ]; then continue; fi
    Rscript run_robyn_mc.R $m $a $ITERS $TRIALS "$OUT" $CORES 2> logs_mc/m${m}_${a}.log
  done
done
echo done > logs_mc/queue_$(echo $MARKETS | tr ' ' '_').flag
