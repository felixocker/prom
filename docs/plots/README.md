# Plots for the PrOM project benchmark

## Contents
* data
  * benchmark-results.ods - precision, recall, and F-measure values for the benchmark
  * benchmark-results.csv - csv export of the respective ods file
  * onto_data.txt - key data, i.e., number of notions and necessary interactions for merging, for the ontologies included in the benchmark
  * timing-results.csv - timing results for the benchmark
* scripts
  * plot_benchmark.py - plot the benchmark results (benchmark-results.csv)
  * plot_timing.py - create a scatter plot and a boxplot for the timing results (timing-results.csv)
  * process_onto_data.py - return ontology data (onto_data.txt) in a LaTeX-friendly way 


# Reproducibility information

## System information

specification of the system used for creating the data above

* OS: Fedora release 33 (Thirty Three) x86_6
* CPU: Intel i7-10510U (8) @ 4.900GHz
* RAM: 16 GB
* Python version: 3.7
* JDK version: 11.0.11

## Code versions used for the benchmarks
* benchmark-results.csv: data for quality assessment was created using code from commit 561afa4
* timing-results.csv: data for timing benchmark was created using the code from commit 56e8926 and the script *tools/time_merge.sh*
