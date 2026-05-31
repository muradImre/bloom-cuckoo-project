Murad Imre - mi15
Probabilistic Filter Experiments
This project runs experiments on Bloom, Counting Bloom, and Cuckoo filters under Zipf-distributed query workloads.

Setup and Run
Create a virtual environment, activate it, install the dependencies, and run the experiments using Python. The experiments are executed with main.py using alpha values of 1.0 and 1.2, a target false positive rate of 0.01, and results written to the results directory. The same experiment can also be run using the provided Makefile.

Output
All results are written to the results directory. 

Experiments
Experiment 1 measures memory usage versus false positive rate. Experiment 2 evaluates lookup latency under Zipf-distributed workloads. Experiment 3 measures end-to-end throughput with and without a filter.

Notes
Memory usage is computed theoretically in bits per key. Backend misses are modeled using a fixed busy-loop cost. Zipf workloads include both members and non-members.