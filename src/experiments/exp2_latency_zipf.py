import csv
import os
import time
import matplotlib.pyplot as plt
import pandas as pd

from src.filters.bloom_filter import BloomFilter
from src.filters.counting_bloom import CountingBloomFilter
from src.filters.cuckoo_filter import CuckooFilter
from src.filters.hashtable_index import HashTableIndex
from src.utils.pipelines import query_with_filter
from src.utils.workloads.dataset import generate_datasets
from src.utils.workloads.zipf_generator import generate_zipf_queries, validate_zipf_queries


def _select_config(df, filter_type, fpr_target):
    subset = df[df["filter_type"] == filter_type]
    subset = subset.iloc[(subset["fpr"] - fpr_target).abs().argsort()]
    if subset.empty:
        raise ValueError(f"No configs for {filter_type}")
    return subset.iloc[0].to_dict()


def _build_filter(config, n_keys):
    ftype = config["filter_type"]
    if ftype == "bloom":
        return BloomFilter(m=int(config["m"]), k=int(config["k"]))
    if ftype == "counting_bloom":
        return CountingBloomFilter(m=int(config["m"]), k=int(config["k"]), counter_bits=int(config["counter_bits"]))
    if ftype == "cuckoo":
        return CuckooFilter(
            num_buckets=int(config["num_buckets"]),
            bucket_size=int(config["bucket_size"]),
            fingerprint_bits=int(config["fingerprint_bits"]),
        )
    raise ValueError(f"Unknown filter_type: {ftype}")


def run_exp2_latency_zipf(alpha=1.0, n_keys=20000, n_queries=50000, fpr_target=0.01, exp1_csv="results/exp1_memory_fpr.csv", output_csv="results/exp2_latency_zipf.csv", non_member_ratio=0.3, seed=42, miss_spins=500):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_configs = pd.read_csv(exp1_csv)

    config_map = {
        ftype: _select_config(df_configs, ftype, fpr_target)
        for ftype in ["bloom", "counting_bloom", "cuckoo"]
    }

    members, non_members = generate_datasets(n_keys, non_member_multiplier=1.0, seed=seed)
    ht = HashTableIndex()
    for key in members:
        ht.insert(key)

    queries = list(generate_zipf_queries(members, alpha, n_queries, non_members, non_member_ratio=non_member_ratio, seed=seed))

    validation = validate_zipf_queries(queries, members, non_members)
    print(f"Zipf validation: non_member_fraction={validation['non_member_fraction']:.3f}, "
          f"top_key={validation['top_frequencies'][0] if validation['top_frequencies'] else 'N/A'}")

    results = []
    for ftype, config in config_map.items():
        filt = _build_filter(config, n_keys)
        for key in members:
            filt.insert(key)

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
                query_with_filter(filt, ht, key, miss_spins=miss_spins)
            total = time.perf_counter() - start
        finally:
            ht.contains = original_contains

        avg_time = total / len(queries)
        backend_per_query = lookup_count / len(queries)

        failed_inserts = getattr(filt, "failed_inserts", None)
        load_factor = None
        if ftype == "cuckoo":
            num_buckets = filt.num_buckets
            bucket_size = filt.bucket_size
            stored = sum(len(bucket) for bucket in filt.buckets)
            load_factor = stored / (num_buckets * bucket_size)

        results.append(
            dict(
                filter_type=ftype,
                alpha=alpha,
                fpr_target=fpr_target,
                avg_time_per_query=avg_time,
                backend_lookups_per_query=backend_per_query,
                n_queries=len(queries),
                config_id=config["config_id"],
                failed_inserts=failed_inserts,
                load_factor=load_factor,
                miss_spins=miss_spins,
            )
        )

    all_fields = {
        "filter_type",
        "alpha",
        "fpr_target",
        "avg_time_per_query",
        "backend_lookups_per_query",
        "n_queries",
        "config_id",
        "failed_inserts",
        "load_factor",
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


def plot_latency(csv_path, fig_path="results/exp2_latency_zipf.png"):
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    df = pd.read_csv(csv_path)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    plt_df = df.sort_values("filter_type")
    plt_df.plot.bar(x="filter_type", y="avg_time_per_query", ax=ax1, legend=False, title="Avg query latency (Zipf)")
    ax1.set_ylabel("seconds per query")
    ax1.set_xlabel("")
    
    plt_df.plot.bar(x="filter_type", y="backend_lookups_per_query", ax=ax2, legend=False, title="Backend lookups per query")
    ax2.set_ylabel("lookups/query")
    ax2.set_xlabel("")
    
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()
    return fig_path


if __name__ == "__main__":
    csv_file = run_exp2_latency_zipf()
    plot_latency(csv_file)
