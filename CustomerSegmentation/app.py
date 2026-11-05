
from pathlib import Path

import pandas as pd
import streamlit as st
from database import get_connection
from datetime import date
# Project folders
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"


def save_segmentation_to_mysql(rfm, kmeans):
    """Save customer segments and a record of this run to MySQL."""

    

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Find the K-means cluster column.
        cluster_column = next(
            (
                col
                for col in [
                    "Cluster",
                    "cluster",
                    "cluster_id",
                    "Cluster_ID",
                    "KMeans_Cluster",
                    "KMeans Cluster",
                ]
                if col in kmeans.columns
            ),
            None,
        )

        
        cluster_lookup = {}
        if cluster_column and "customer_code" in kmeans.columns:
            cluster_lookup = dict(
                zip(
                    kmeans["customer_code"].astype(str),
                    kmeans[cluster_column],
                )
            )
        def number(value, default=0):
            return default if pd.isna(value) else value
        def get_value(row, names, default=None):
            for name in names:
                if name in row.index and pd.notna(row[name]):
                    return row[name]
            return default

        for _, row in rfm.iterrows():
            customer_code = str(row["customer_code"])

            purchase_date = get_value(
                row, ["LastPurchase", "last_purchase_date", "LastPurchaseDate"]
            )
            if purchase_date is not None:
                purchase_date = pd.to_datetime(purchase_date).date()

            r_score = number(get_value(row, ["R_Score", "R Score", "R_Score"]))
            f_score = number(get_value(row, ["F_Score", "F Score", "F_Score"]))
            m_score = number(get_value(row, ["M_Score", "M Score", "M_Score"]))
            cluster = cluster_lookup.get(customer_code)
            cluster_id = (
                None if cluster is None or pd.isna(cluster)
                else int(cluster)
            )

            cursor.execute(
                """
                INSERT INTO customers
                    (customer_id, last_purchase_date, frequency,
                     monetary, recency, r_score, f_score, m_score,
                     segment, cluster_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_purchase_date = VALUES(last_purchase_date),
                    frequency = VALUES(frequency),
                    monetary = VALUES(monetary),
                    recency = VALUES(recency),
                    r_score = VALUES(r_score),
                    f_score = VALUES(f_score),
                    m_score = VALUES(m_score),
                    segment = VALUES(segment),
                    cluster_id = VALUES(cluster_id)
                """,
                (
                    customer_code,
                    purchase_date,
                    int(row["Frequency"]),
                    float(row["Monetary"]),
                    int(row["Recency"]),
                    int(r_score),
                    int(f_score),
                    int(m_score),
                    str(row["Segment"]),
                    cluster_id,
                ),
            )

        cursor.execute(
            """
            INSERT INTO segmentation_runs
                (total_customers, method, silhouette_score)
            VALUES (%s, %s, %s)
            """,
            (len(rfm), "RFM + K-means", None),
        )

        connection.commit()
        return len(rfm)

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

# Page configuration
st.set_page_config(
    page_title="Customer Segmentation Dashboard",
    page_icon="📊",
    layout="wide",
)

# Dashboard heading
st.title("📊 Customer Segmentation and Predictive Analytics")
st.write(
    "Explore customer purchase behavior using RFM analysis "
    "and K-means clustering."
)

# Load generated project results
@st.cache_data
def load_data():
    rfm = pd.read_csv(OUTPUT_DIR / "rfm_table.csv")
    profiles = pd.read_csv(OUTPUT_DIR / "segment_profiles.csv")
    kmeans = pd.read_csv(
        OUTPUT_DIR / "kmeans_customer_segments.csv"
    )
    kmeans_profiles = pd.read_csv(
        OUTPUT_DIR / "kmeans_profiles.csv"
    )
    return rfm, profiles, kmeans, kmeans_profiles


try:
    rfm, profiles, kmeans, kmeans_profiles = load_data()
except FileNotFoundError:
    st.error(
        "Project output files are missing. "
        "Run 'python main.py' in the VS Code terminal first."
    )
    st.stop()

# Sidebar filters
st.sidebar.header("Customer Filters")

segments = sorted(rfm["Segment"].dropna().unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Select RFM segments",
    segments,
    default=segments,
)

min_spend = float(rfm["Monetary"].min())
max_spend = float(rfm["Monetary"].max())

spending_range = st.sidebar.slider(
    "Total spending range",
    min_value=min_spend,
    max_value=max_spend,
    value=(min_spend, max_spend),
)

filtered = rfm[
    rfm["Segment"].isin(selected_segments)
    & rfm["Monetary"].between(
        spending_range[0], spending_range[1]
    )
].copy()

# Key performance indicators
st.subheader("Customer Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Customers", len(rfm))
c2.metric("Filtered Customers", len(filtered))
c3.metric(
    "Average Spending",
    f"₹{rfm['Monetary'].mean():,.2f}",
)
c4.metric(
    "Average Recency",
    f"{rfm['Recency'].mean():.1f} days",
)

# Main dashboard tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "RFM Analysis",
        "K-means Clustering",
        "Customer Explorer",
        "Downloads",
        "MySQL Database",
    ]
)

with tab1:
    st.subheader("Rule-Based RFM Segments")
    st.caption(
        "Segments are assigned using the business rules "
        "defined in rfm_analysis.py."
    )

    st.dataframe(profiles, use_container_width=True)

    chart_path = OUTPUT_DIR / "rfm_distribution.png"
    if chart_path.exists():
        st.image(
            str(chart_path),
            caption="Distribution of rule-based RFM segments",
            use_container_width=True,
        )

    scatter_path = OUTPUT_DIR / "rfm_scatter.png"
    if scatter_path.exists():
        st.image(
            str(scatter_path),
            caption="Customer frequency versus spending",
            use_container_width=True,
        )

with tab2:
    st.subheader("K-means Clustering Results")

    st.write(
        "K-means groups customers using standardized "
        "recency, frequency, and monetary features."
    )

    st.dataframe(
        kmeans_profiles,
        use_container_width=True,
    )

    eval_path = OUTPUT_DIR / "kmeans_evaluation.csv"
    if eval_path.exists():
        evaluation = pd.read_csv(eval_path)
        st.write("Candidate cluster-count evaluation")
        st.dataframe(evaluation, use_container_width=True)

    cluster_chart = OUTPUT_DIR / "kmeans_distribution.png"
    if cluster_chart.exists():
        st.image(
            str(cluster_chart),
            caption="Number of customers in each cluster",
            use_container_width=True,
        )

    compare_chart = OUTPUT_DIR / "spending_comparison.png"
    if compare_chart.exists():
        st.image(
            str(compare_chart),
            caption="Average spending comparison",
            use_container_width=True,
        )

    st.info(
        "Cluster IDs are arbitrary labels. Interpret them using "
        "their average RFM values, not by the ID number alone."
    )


with tab3:
    st.subheader("Explore Individual Customers")

    st.write(f"Showing {len(filtered)} matching customers.")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    if not filtered.empty:
        search_code = st.text_input(
            "Search customer code",
            placeholder="Enter a customer code...",
        )

        customer_codes = filtered["customer_code"].astype(str).tolist()

        if search_code.strip():
            matching_codes = [
                code for code in customer_codes
                if search_code.strip().lower() in code.lower()
            ]
        else:
            matching_codes = customer_codes

        if matching_codes:
            chosen_customer = st.selectbox(
                "Select a customer",
                matching_codes,
            )

            customer = filtered[
                filtered["customer_code"].astype(str) == chosen_customer
            ].iloc[0]

            a, b, c = st.columns(3)
            a.metric("Recency", f"{customer['Recency']} days")
            b.metric("Frequency", int(customer["Frequency"]))
            c.metric("Monetary", f"₹{customer['Monetary']:,.2f}")

            st.write(f"**Rule-based segment:** {customer['Segment']}")
        else:
            st.warning("No matching customer found.")
    else:
        st.info("No customers match the selected filters.")

with tab4:
    st.subheader("Download Project Results")

    st.download_button(
        "Download filtered RFM data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_rfm_customers.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download all RFM results",
        data=rfm.to_csv(index=False).encode("utf-8"),
        file_name="rfm_table.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download K-means results",
        data=kmeans.to_csv(index=False).encode("utf-8"),
        file_name="kmeans_customer_segments.csv",
        mime="text/csv",
    )

    comparison_path = OUTPUT_DIR / "method_comparison.csv"
    if comparison_path.exists():
        comparison = pd.read_csv(comparison_path)
        st.download_button(
            "Download method comparison",
            data=comparison.to_csv(index=False).encode("utf-8"),
            file_name="method_comparison.csv",
            mime="text/csv",
        )

st.divider()
st.caption(
    "Educational project using anonymized sample data. "
    "Customer segments describe historical behavior and "
    "do not guarantee future purchases."
)


with tab5:
    st.subheader("MySQL Database")

    st.write(
        "Save customer segments and view saved records."
    )

    try:
        connection = get_connection()

        saved_customers = pd.read_sql(
            "SELECT * FROM customers ORDER BY customer_id",
            connection,
        )

        run_history = pd.read_sql(
            "SELECT * FROM segmentation_runs ORDER BY run_id DESC",
            connection,
        )

        connection.close()

        # Database summary
        st.success("MySQL connected successfully!")

        c1, c2 = st.columns(2)
        c1.metric("Saved Customers", len(saved_customers))
        c2.metric("Segmentation Runs", len(run_history))

        # Save button
        if st.button("Save Segmentation Results to MySQL"):
            try:
                with st.spinner("Saving customer data..."):
                    saved_count = save_segmentation_to_mysql(rfm, kmeans)

                st.success(
                    f"Successfully saved {saved_count} customer records!"
                )
                st.rerun()

            except Exception as error:
                st.error(f"Could not save to MySQL: {error}")

        # Refresh button
        if st.button("Refresh Database Records"):
            st.rerun()

        # Display saved records
        st.subheader("Saved Customers")
        st.dataframe(
            saved_customers,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Segmentation Run History")
        st.dataframe(
            run_history,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"MySQL connection or data loading failed: {error}")
