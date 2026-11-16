#!/bin/bash
# Resumable wrapper: runs real Robyn market by market (both frequencies), skipping markets already in the output file.
cd "$(dirname "$0")"
OUT=results/RBREAL_1000_full.csv
for m in 0 4 6 10 12 16 18 22 24 28 30 34; do
  if [ -f $OUT ] && [ $(awk -F, -v m=$m 'NR>1 && $1==m' $OUT | wc -l) -ge 2 ]; then continue; fi
  Rscript run_robyn_real.R 1000 results/RBREAL_tmp_$m.csv $m 2> rbreal_m$m.log
  cat results/RBREAL_tmp_$m.csv | awk -v f=$([ -f $OUT ] && echo 0 || echo 1) 'NR>1 || f==1' >> $OUT
  rm -f results/RBREAL_tmp_$m.csv
done
echo ALLDONE > rbreal_done.flag
