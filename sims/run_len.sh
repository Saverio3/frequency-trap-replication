#!/bin/bash
cd "$(dirname "$0")"
nice -n 19 python dec_run.py len 78 300 > dec_len78.log 2>&1
nice -n 19 python dec_run.py len 260 300 > dec_len260.log 2>&1
echo done > dec_len.flag
