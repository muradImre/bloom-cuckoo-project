import csv
import math
import os
import matplotlib.pyplot as plt
import pandas as pd

from src.filters.bloom_filter import BloomFilter
from src.filters.counting_bloom import CountingBloomFilter
from src.filters.cuckoo_filter import CuckooFilter
from src.utils.workloads.dataset import generate_datasets
from src.utils.memory import bits_per_key


def _measure_fpr(filter_obj, non_members):
    false_positives = sum(1 for key in non_members if filter_obj.contains(key))
    return false_positives / len(non_members)


def run_exp1_memory_vs_fpr(n_keys=20000, non_member_multiplier=2.0, output_csv="results/exp1_memory_fpr.csv", seed=42):
    members, non_members = generate_datasets(n_keys, non_member_multiplier, seed=seed)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    rows = []

    for fp_target in [0.1, 0.05, 0.02, 0.01, 0.005]:
        bf = BloomFilter(n=n_keys, fp_target=fp_target)
        for key in members:
            bf.insert(key)
        fpr = _measure_fpr(bf, non_members)
        mem = bf.memory_bytes()
        rows.append(
            dict(
                filter_type="bloom",
                config_id=f"bf_fp_{fp_target}",
                fpr=fpr,
                memory_bytes=mem,
                bits_per_key=bits_per_key(mem, n_keys),
                m=bf.m,
                k=bf.k,
                counter_bits=None,
                fingerprint_bits=None,
                bucket_size=None,
                num_buckets=None,
            )
        )

    for fp_target in [0.05, 0.02, 0.01]:
        for counter_bits in [4, 8]:
            cbf = CountingBloomFilter(n=n_keys, fp_target=fp_target, counter_bits=counter_bits)
            for key in members:
                cbf.insert(key)
            fpr = _measure_fpr(cbf, non_members)
            mem = cbf.memory_bytes()
            rows.append(
                dict(
                    filter_type="counting_bloom",
                    config_id=f"cbf_fp_{fp_target}_c{counter_bits}",
                    fpr=fpr,
                    memory_bytes=mem,
                    bits_per_key=bits_per_key(mem, n_keys),
                    m=cbf.m,
                    k=cbf.k,
                    counter_bits=counter_bits,
                    fingerprint_bits=None,
                    bucket_size=None,
                    num_buckets=None,
                )
            )

    bucket_size = 4
    num_buckets = int(math.ceil(n_keys / (bucket_size * 0.9)))
    for fp_bits in [8, 12, 16]:
        cf = CuckooFilter(num_buckets=num_buckets, bucket_size=bucket_size, fingerprint_bits=fp_bits)
        for key in members:
            cf.insert(key)
        fpr = _measure_fpr(cf, non_members)
        mem = cf.memory_bytes()
        load_factor = sum(len(bucket) for bucket in cf.buckets) / (num_buckets * bucket_size)
        rows.append(
            dict(
                filter_type="cuckoo",
                config_id=f"cf_fpbits_{fp_bits}",
                fpr=fpr,
                memory_bytes=mem,
                bits_per_key=bits_per_key(mem, n_keys),
                m=None,
                k=None,
                counter_bits=None,
                fingerprint_bits=fp_bits,
                bucket_size=bucket_size,
                num_buckets=num_buckets,
                failed_inserts=cf.failed_inserts,
                load_factor=load_factor,
            )
        )

    all_fields = {
        "filter_type",
        "config_id",
        "fpr",
        "memory_bytes",
        "bits_per_key",
        "m",
        "k",
        "counter_bits",
        "fingerprint_bits",
        "bucket_size",
        "num_buckets",
        "failed_inserts",
        "load_factor",
    }
    for row in rows:
        for field in all_fields:
            if field not in row:
                row[field] = None

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
        writer.writeheader()
        writer.writerows(rows)

    return output_csv


def plot_memory_vs_fpr(csv_path, fig_path="results/exp1_memory_fpr.png"):
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    df = pd.read_csv(csv_path)
    plt.figure(figsize=(8, 5))
    for ftype, marker in [("bloom", "o"), ("counting_bloom", "s"), ("cuckoo", "x")]:
        subset = df[df["filter_type"] == ftype].sort_values("bits_per_key")
        plt.plot(subset["bits_per_key"], subset["fpr"], marker=marker, linestyle="-", label=ftype)
    plt.yscale("log")
    plt.xlabel("bits per key")
    plt.ylabel("false positive rate")
    plt.title("Memory vs FPR")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()
    return fig_path


if __name__ == "__main__":
    csv_file = run_exp1_memory_vs_fpr()
    plot_memory_vs_fpr(csv_file)
