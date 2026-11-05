from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

def create_charts(rfm, kmeans_result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rfm["Segment"].value_counts().plot(kind="bar", figsize=(9, 5))
    plt.title("Rule-Based RFM Segment Distribution")
    plt.xlabel("Segment")
    plt.ylabel("Number of Customers")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "rfm_distribution.png", dpi=150)
    plt.close()

    kmeans_result["KMeansCluster"].value_counts().sort_index().plot(kind="bar", figsize=(8, 5))
    plt.title("K-Means Cluster Distribution")
    plt.xlabel("Cluster ID (arbitrary label)")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "kmeans_distribution.png", dpi=150)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    rfm.groupby("Segment")["Monetary"].mean().plot(kind="bar", ax=axes[0])
    axes[0].set_title("Average Spending: RFM Rules")
    axes[0].set_ylabel("Average Spending")
    axes[0].set_xlabel("Segment")
    axes[0].tick_params(axis="x", rotation=30)

    kmeans_result.groupby("KMeansCluster")["Monetary"].mean().plot(kind="bar", ax=axes[1])
    axes[1].set_title("Average Spending: K-Means")
    axes[1].set_ylabel("Average Spending")
    axes[1].set_xlabel("Cluster ID")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "spending_comparison.png", dpi=150)
    plt.close()

    # RFM scatter plot, colored by rule-based label
    fig, ax = plt.subplots(figsize=(8, 6))
    for label, group in rfm.groupby("Segment"):
        ax.scatter(group["Frequency"], group["Monetary"], label=label, s=55)
    ax.set_title("Customer Purchase Frequency vs Spending")
    ax.set_xlabel("Frequency (distinct completed orders)")
    ax.set_ylabel("Monetary value")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "rfm_scatter.png", dpi=150)
    plt.close()

    print("Charts saved in the outputs folder.")
