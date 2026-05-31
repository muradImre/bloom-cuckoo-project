import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

from src.experiments.exp1_memory_fpr import run_exp1_memory_vs_fpr
from src.experiments.exp2_latency_zipf import run_exp2_latency_zipf
from src.experiments.exp3_throughput import run_exp3_throughput


def get_configs(csv_path, fpr_target):
    df = pd.read_csv(csv_path)
    configs = {}
    for ftype in ["bloom", "counting_bloom", "cuckoo"]:
        rows = df[df["filter_type"] == ftype]
        best = rows.iloc[(rows["fpr"] - fpr_target).abs().argsort()].iloc[0]
        configs[ftype] = best.to_dict()
    return configs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alphas", default="1.0,1.2")
    parser.add_argument("--fpr_targets", default="0.01")
    parser.add_argument("--results_dir", default="results")
    args = parser.parse_args()

    alphas = [float(x.strip()) for x in args.alphas.split(",") if x.strip()]
    fpr_targets = [float(x.strip()) for x in args.fpr_targets.split(",") if x.strip()]

    os.makedirs(args.results_dir, exist_ok=True)

    print("Running Exp1...")
    exp1_csv = f"{args.results_dir}/exp1_memory_fpr.csv"
    run_exp1_memory_vs_fpr(output_csv=exp1_csv)
    
    df = pd.read_csv(exp1_csv)
    plt.figure(figsize=(8, 5))
    for ftype, marker in [("bloom", "o"), ("counting_bloom", "s"), ("cuckoo", "x")]:
        rows = df[df["filter_type"] == ftype].sort_values("bits_per_key")
        plt.plot(rows["bits_per_key"], rows["fpr"], marker=marker, label=ftype)
    plt.yscale("log")
    plt.xlabel("bits per key")
    plt.ylabel("false positive rate")
    plt.title("Memory vs FPR")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{args.results_dir}/exp1_memory_fpr.png")
    plt.close()

    for fpr_target in fpr_targets:
        configs = get_configs(exp1_csv, fpr_target)

        for alpha in alphas:
            print(f"Running Exp2... alpha={alpha}, fpr={fpr_target}")
            exp2_csv = f"{args.results_dir}/exp2_latency_zipf_alpha{alpha}_fpr{fpr_target}.csv"
            run_exp2_latency_zipf(alpha=alpha, exp1_csv=exp1_csv, output_csv=exp2_csv, fpr_target=fpr_target, seed=42, miss_spins=500)
            
            df2 = pd.read_csv(exp2_csv)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            df2.plot.bar(x="filter_type", y="avg_time_per_query", ax=ax1, legend=False, title="Avg query latency (Zipf)")
            ax1.set_ylabel("seconds per query")
            df2.plot.bar(x="filter_type", y="backend_lookups_per_query", ax=ax2, legend=False, title="Backend lookups per query")
            ax2.set_ylabel("lookups/query")
            plt.tight_layout()
            plt.savefig(f"{args.results_dir}/exp2_latency_zipf_alpha{alpha}_fpr{fpr_target}.png")
            plt.close()

            print(f"Running Exp3... alpha={alpha}, fpr={fpr_target}")
            exp3_csv = f"{args.results_dir}/exp3_throughput_alpha{alpha}_fpr{fpr_target}.csv"
            run_exp3_throughput(alpha=alpha, config_map=configs, output_csv=exp3_csv, seed=42, miss_spins=500)
            
            df3 = pd.read_csv(exp3_csv)
            df3.plot.bar(x="pipeline_type", y="throughput_qps", legend=False, title="Throughput by pipeline")
            plt.ylabel("queries/sec")
            plt.tight_layout()
            plt.savefig(f"{args.results_dir}/exp3_throughput_alpha{alpha}_fpr{fpr_target}.png")
            plt.close()
            
            df3.plot.bar(x="pipeline_type", y="backend_lookups_per_query", legend=False, title="Backend lookups per query")
            plt.ylabel("lookups/query")
            plt.tight_layout()
            plt.savefig(f"{args.results_dir}/exp3_backend_alpha{alpha}_fpr{fpr_target}.png")
            plt.close()

    print(f"Done. Results in {args.results_dir}")


if __name__ == "__main__":
    main()

