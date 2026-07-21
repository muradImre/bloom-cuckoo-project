# Network Cache Lookup Optimization

This project compares Bloom, Counting Bloom, and Cuckoo filters as cache
pre-filters under Zipf-distributed query workloads.

## Experiments

- Memory usage versus false-positive rate
- Lookup latency and backend lookup frequency
- End-to-end throughput against a no-filter baseline

The full methodology, results, and conclusions are available in the
[project report](project-report.pdf).

## Setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Run the default experiment suite:

```sh
make run
```

Alternatively, invoke the script directly and customize its parameters:

```sh
python main.py \
  --alphas 1.0,1.2 \
  --fpr_targets 0.01 \
  --results_dir results
```

Generated CSV files and plots are written to `results/`.

## Methodology notes

- Memory usage is calculated theoretically in bits per key.
- Backend misses are modeled with a fixed busy-loop cost.
- Workloads include both member and non-member queries.

## Author

Murad Imre (`mi15`)