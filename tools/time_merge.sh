#!/bin/bash

# run and time main.py, return execution times in seconds separated by commas
# NOTE: make sure to set up the config file correctly; possibly comment out abox merging in main.py
# NOTE: uncomment code below as needed for MEXT/ MEXO, MVSP, and OAEI examples; place respective ontos in tools/
# Usage: bash time_merge.sh iterations

iterations="$1"
RES=""

# default to 10 iterations if variable is not set
if [ -z "$iterations" ]; then
	echo "time_merge: iterations variable not set, defaulting to 10"
	iterations=10
fi

# setup
source ../.venv/bin/activate
cd ../src/
TIMEFORMAT="%R"

# timing
for n in $(seq $iterations); do
	echo "iteration: $n"
  # MEXT/ MEXO; works with "config_min.yml", set min-example to False
  # MEXO: translate onto-fr using translate_onto.py
  cp ../tools/*.owl ../data/
  # MVSP; works with "alt_config.yml"
  # cp ../tools/manufacturing-capability ../tools/mason_reduced.owl ../data/
  # OAEI; works with "config_YYY.yml"; set reject threshold to .6 for automatic mode
  # cp ../tools/*.rdf ../data/
	exec 3>&1 4>&2
	TIMING=$( { time python main.py 1>&3 2>&4; } 2>&1 )
	exec 3>&- 4>&-
	echo "timing result for iteration $n: $TIMING"
	RES+="${RES:+,}$TIMING"
	rm ../data/*.owl ../data/manufacturing-capability ../data/*.rdf
done

# reset
rm ./*.log
unset TIMEFORMAT

# return results
printf "overall timing results:\n$RES\n"
