#!/bin/bash
cd "$(dirname "$0")"
nice -n 19 python dec_run.py len 156 300 > dec_len156.log 2>&1
nice -n 19 python dec_shallow.py main 300 > dsh_main.log 2>&1
echo done > dec_len2.flag
