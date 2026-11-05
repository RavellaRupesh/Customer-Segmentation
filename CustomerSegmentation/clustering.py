from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

def run_clustering(rfm, n_clusters=3):
    """Run K-means on scaled RFM features and save profiles/evaluation."""
    features = ["Recency", "Frequency", "Monetary"]
    X = rfm[features].astype(float)

    if len(X) <= n_clusters:
        raise ValueError("The number of customers must be greater than n_clusters.")
    if X.nunique().min() == 1:
        print("Note: At least one RFM feature has no variation in this dataset.")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(X_scaled)
    result = rfm.copy()
    result["KMeansCluster"] = labels

    unique_labels = np.unique(labels)
    score = None
    if 1 < len(unique_labels) < len(X):
        score = float(silhouette_score(X_scaled, labels))
        print(f"\nSilhouette score (k={n_clusters}): {score:.3f}")
    else:
        print("Silhouette score is undefined for this clustering result.")

    profiles = result.groupby("KMeansCluster", as_index=False).agg(
        CustomerCount=("customer_code", "count"),
        AverageRecency=("Recency", "mean"),
        AverageFrequency=("Frequency", "mean"),
        AverageSpending=("Monetary", "mean"),
        TotalSpending=("Monetary", "sum"),
    ).round(2)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_DIR / "kmeans_customer_segments.csv", index=False)
    profiles.to_csv(OUTPUT_DIR / "kmeans_profiles.csv", index=False)

    # Evaluate a small range of candidate cluster counts when possible.
    evaluation_rows = []
    max_k = min(5, len(X) - 1)
    for k in range(2, max_k + 1):
        candidate_labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_scaled)
        if 1 < len(np.unique(candidate_labels)) < len(X):
            evaluation_rows.append({
                "k": k,
                "silhouette_score": round(float(silhouette_score(X_scaled, candidate_labels)), 4)
            })
    pd.DataFrame(evaluation_rows).to_csv(OUTPUT_DIR / "kmeans_evaluation.csv", index=False)

    print("\n=== K-MEANS CLUSTER PROFILES ===")
    print(profiles.to_string(index=False))
    print("\nCandidate k evaluation saved to outputs/kmeans_evaluation.csv")
    return result, profiles, score

if __name__ == "__main__":
    from rfm_analysis import calculate_rfm
    rfm, _ = calculate_rfm()
    run_clustering(rfm)
