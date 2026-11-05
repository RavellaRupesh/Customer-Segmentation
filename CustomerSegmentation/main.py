from pathlib import Path
import pandas as pd
from rfm_analysis import calculate_rfm
from clustering import run_clustering
from visualization import create_charts

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

def main():
    print("=" * 60)
    print("CUSTOMER SEGMENTATION AND PREDICTIVE ANALYTICS SYSTEM")
    print("=" * 60)
    print("Data source: anonymized sample CSV")
    print("Analysis date: 2026-10-28 (fixed for reproducible sample results)")

    rfm, _ = calculate_rfm(analysis_date="2026-10-28")
    kmeans_result, _, score = run_clustering(rfm, n_clusters=3)
    create_charts(rfm, kmeans_result)

    comparison = rfm[["customer_code", "Segment"]].merge(
        kmeans_result[["customer_code", "KMeansCluster"]],
        on="customer_code",
        how="inner",
    )
    comparison.to_csv(OUTPUT_DIR / "method_comparison.csv", index=False)

    summary = pd.DataFrame([{
        "analysis_date": "2026-10-28",
        "customer_count": len(rfm),
        "kmeans_clusters": 3,
        "silhouette_score": score,
        "note": "Cluster IDs are arbitrary; interpret using cluster profiles."
    }])
    summary.to_csv(OUTPUT_DIR / "run_summary.csv", index=False)

    print("\n=== METHOD COMPARISON (first 10 customers) ===")
    print(comparison.head(10).to_string(index=False))
    print("\nDone. Open the outputs folder to view CSV files and charts.")
    print("Reminder: these groups describe observed behavior, not guaranteed future actions.")

if __name__ == "__main__":
    main()
