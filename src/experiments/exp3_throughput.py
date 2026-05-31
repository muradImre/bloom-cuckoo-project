import csv
import os
import time
import matplotlib.pyplot as plt
import pandas as pd

from src.filters.bloom_filter import BloomFilter
from src.filters.counting_bloom import CountingBloomFilter
from src.filters.cuckoo_filter import CuckooFilter
from src.filters.hashtable_index import HashTableIndex
from src.utils.pipelines import query_no_filter, query_with_filter
from src.utils.workloads.dataset import generate_datasets
from src.utils.workloads.zipf_generator import generate_zipf_queries, validate_zipf_queries


def _build_filter(filter_type, config):
    if filter_type == "bloom":
        return BloomFilter(m=int(config["m"]), k=int(config["k"]))
    if filter_type == "counting_bloom":
        return CountingBloomFilter(m=int(config["m"]), k=int(config["k"]), counter_bits=int(config["counter_bits"]))
    if filter_type == "cuckoo":
        return CuckooFilter(
            num_buckets=int(config["num_buckets"]),
            bucket_size=int(config["bucket_size"]),
            fingerprint_bits=int(config["fingerprint_bits"]),
        )
    raise ValueError(f"Unknown filter_type: {filter_type}")


def run_exp3_throughput(alpha=1.0, n_keys=20000, n_queries=50000, config_map=None, output_csv="results/exp3_throughput.csv", non_member_ratio=0.3, seed=42, miss_spins=500):
    if config_map is None:
        raise ValueError("config_map required for exp3")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    members, non_members = generate_datasets(n_keys, non_member_multiplier=1.0, seed=seed)
    ht = HashTableIndex()
    for key in members:
        ht.insert(key)

    queries = list(generate_zipf_queries(members, alpha, n_queries, non_members, non_member_ratio=non_member_ratio, seed=seed))

    validation = validate_zipf_queries(queries, members, non_members)
    print(f"Zipf validation: non_member_fraction={validation['non_member_fraction']:.3f}, "
          f"top_key={validation['top_frequencies'][0] if validation['top_frequencies'] else 'N/A'}")

    results = []

    lookup_count = 0

    original_contains = ht.contains

    def counted_contains(k):
        nonlocal lookup_count
        lookup_count += 1
        return original_contains(k)

    ht.contains = counted_contains
    try:
        start = time.perf_counter()
        for key in queries:
            query_no_filter(ht, key, miss_spins=miss_spins)
        total = time.perf_counter() - start
    finally:
        ht.contains = original_contains

    results.append(
        dict(
            pipeline_type="no_filter",
            alpha=alpha,
            avg_time_per_query=total / len(queries),
            throughput_qps=len(queries) / total,
            backend_lookups_per_query=lookup_count / len(queries),
            n_queries=len(queries),
            miss_spins=miss_spins,
        )
    )

    for ftype, cfg in config_map.items():
        filt = _build_filter(ftype, cfg)
        for key in members:
            filt.insert(key)

        lookup_count = 0
        original_contains = ht.contains

        def counted_contains_filter(k):
            nonlocal lookup_count
            lookup_count += 1
            return original_contains(k)

        ht.contains = counted_contains_filter

        try:
            start = time.perf_counter()
            for key in queries:
                query_with_filter(filt, ht, key, miss_spins=miss_spins)
            total = time.perf_counter() - start
        finally:
            ht.contains = original_contains

        results.append(
            dict(
                pipeline_type=f"{ftype}+ht",
                alpha=alpha,
                avg_time_per_query=total / len(queries),
                throughput_qps=len(queries) / total,
                backend_lookups_per_query=lookup_count / len(queries),
                n_queries=len(queries),
                miss_spins=miss_spins,
            )
        )

    all_fields = {
        "pipeline_type",
        "alpha",
        "avg_time_per_query",
        "throughput_qps",
        "backend_lookups_per_query",
        "n_queries",
        "miss_spins",
    }
    for row in results:
        for field in all_fields:
            if field not in row:
                row[field] = None

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
        writer.writeheader()
        writer.writerows(results)

    return output_csv


def plot_throughput(csv_path, fig_path="results/exp3_throughput.png"):
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    df = pd.read_csv(csv_path)
    plt_df = df.sort_values("pipeline_type")
    ax = plt_df.plot.bar(x="pipeline_type", y="throughput_qps", title="Throughput by pipeline", legend=False)
    ax.set_ylabel("queries/sec")
    ax.set_xlabel("")
    ax.figure.tight_layout()
    ax.figure.savefig(fig_path)
    plt.close()
    return fig_path


def plot_backend_lookups(csv_path, fig_path="results/exp3_backend_lookups.png"):
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    df = pd.read_csv(csv_path)
    plt_df = df.sort_values("pipeline_type")
    ax = plt_df.plot.bar(
        x="pipeline_type",
        y="backend_lookups_per_query",
        title="Backend lookups per query",
        legend=False,
    )
    ax.set_ylabel("lookups/query")
    ax.set_xlabel("")
    ax.figure.tight_layout()
    ax.figure.savefig(fig_path)
    plt.close()
    return fig_path


if __name__ == "__main__":
    raise SystemExit("Use run_main_experiment to supply config_map from Exp1.")
