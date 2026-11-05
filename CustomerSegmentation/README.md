# Customer Segmentation and Predictive Analytics System

An educational Data Science project that groups anonymized customers using Recency, Frequency, and Monetary value (RFM), then compares transparent rule-based segments with K-means clusters.

## Features
- Anonymized sample purchase data in `data/orders.csv`
- RFM feature engineering using Pandas
- Explicit, interpretable rule-based segments
- Optional K-means clustering with StandardScaler
- Silhouette-score evaluation for candidate cluster counts
- CSV outputs and Matplotlib charts
- MySQL schema and optional connection helper

## Requirements
- Python 3.10 or newer recommended
- VS Code
- MySQL Server / MySQL Workbench only if using the optional database component

## Run in Windows VS Code
Open this folder in VS Code, then open Terminal > New Terminal.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, use Command Prompt and run:
```bat
.venv\Scripts\activate.bat
```

After running, check `outputs/` for:
- `rfm_table.csv`
- `segment_profiles.csv`
- `kmeans_customer_segments.csv`
- `kmeans_profiles.csv`
- `kmeans_evaluation.csv`
- `method_comparison.csv`
- `run_summary.csv`
- PNG charts

## Data definitions
- Recency: days between the fixed analysis date (2026-10-28) and the customer's latest completed purchase.
- Frequency: number of distinct completed orders.
- Monetary: sum of quantity multiplied by unit price for completed order lines.
- Cancelled orders are excluded.
- The fixed analysis date makes the included sample results reproducible. Change it in `main.py` for a different analysis date.

## Rule-based segments
The thresholds in `rfm_analysis.py` are illustrative and should be justified or tuned for a real dataset:
- High-Value Active: Recency <= 30, Frequency >= 3, Monetary >= 2000
- At Risk / Inactive: Recency > 90
- New or One-Time: Frequency == 1
- Regular / Developing: remaining customers

These categories are not objective truths; they depend on the analysis date, data coverage, and chosen thresholds.

## K-means design
- Input features: Recency, Frequency, Monetary
- Features are standardized using `StandardScaler`
- Default cluster count: 3, used as a starting point rather than a proven optimum
- Candidate k values are evaluated with silhouette scores in `outputs/kmeans_evaluation.csv`
- Cluster IDs are arbitrary. Inspect cluster profiles before describing a group.

A silhouette score measures how well clusters separate in feature space; it does not establish business usefulness or predict future purchases. K-means is clustering, not predictive modeling by itself.

## Optional MySQL database
1. Start MySQL Server.
2. Open `schema.sql` in MySQL Workbench and execute it.
3. Set your password in the terminal, for example in PowerShell:
   `$env:DB_PASSWORD = "your-local-mysql-password"`
4. Use `database.py` as the connection helper when adding database import/query logic.

The current runnable analysis reads the sample CSV. The MySQL schema and connection helper are provided as the database integration starting point; CSV-to-MySQL loading and storing each run's segment labels must be implemented to make the database the live data source.

## Limitations
- Included data is small and synthetic; it is not suitable for real business decisions.
- Segment assignments depend on the selected thresholds and analysis date.
- K-means depends on scaling, features, initialization, and cluster count.
- A segment describes historical purchase behavior and does not guarantee future behavior.
- To add genuine predictive analytics, define a future outcome (for example, purchase within 30 days), train a supervised model, and evaluate it on held-out data.
