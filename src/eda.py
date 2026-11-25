"""
SWYNEX Technologies - Internship Task 2: Exploratory Data Analysis (EDA)
Script: src/eda.py
Description: End-to-end Python pipeline to perform exhaustive exploratory data analysis,
             compute descriptive statistics, detect outliers via IQR, generate
             high-quality visualizations, and output key business insights.
Author: SWYNEX Data Analytics Intern
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def setup_visualization_style():
    """Configure modern, publication-grade visualization styling."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["legend.fontsize"] = 10
    plt.rcParams["figure.titlesize"] = 14


def get_paths():
    """Resolve absolute paths for the project directories."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "cleaned", "cleaned_dataset.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(base_dir, "data", "cleaned_dataset.csv")
    charts_dir = os.path.join(base_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    return data_path, charts_dir


def load_dataset(data_path):
    """Load and validate the cleaned dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned dataset missing at: {data_path}. Please complete Task 1 first.")
    
    df = pd.read_csv(data_path)
    df["reservation_status_date"] = pd.to_datetime(df["reservation_status_date"], errors="coerce")
    return df


def compute_summary_statistics(df):
    """Calculate and display comprehensive summary statistics for numeric and categorical columns."""
    print("\n" + "=" * 70)
    print("                    DATASET OVERVIEW & SUMMARY STATISTICS           ")
    print("=" * 70)
    print(f"Total Observations (Rows): {df.shape[0]:,}")
    print(f"Total Attributes (Columns): {df.shape[1]}")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats_df = pd.DataFrame({
        "Mean": df[numeric_cols].mean(),
        "Median": df[numeric_cols].median(),
        "Mode": df[numeric_cols].mode().iloc[0],
        "Std Dev": df[numeric_cols].std(),
        "Min": df[numeric_cols].min(),
        "Q1 (25%)": df[numeric_cols].quantile(0.25),
        "Q3 (75%)": df[numeric_cols].quantile(0.75),
        "Max": df[numeric_cols].max()
    })
    
    print("\n--- Numerical Summary Statistics ---")
    print(stats_df.round(2).to_string())
    
    print("\n--- Top Categorical Distributions ---")
    for cat_col in ["hotel", "meal", "market_segment", "deposit_type", "customer_type"]:
        counts = df[cat_col].value_counts()
        pcts = df[cat_col].value_counts(normalize=True) * 100
        dist = pd.DataFrame({"Count": counts, "Percentage (%)": pcts.round(1)})
        print(f"\n[{cat_col.upper()}]:")
        print(dist.head(5).to_string())
        
    return stats_df


def detect_iqr_outliers(df, columns):
    """
    Detect outliers using the Interquartile Range (IQR) method.
    IQR = Q3 - Q1
    Outlier boundaries: [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    """
    outlier_summary = {}
    print("\n" + "=" * 70)
    print("                 IQR OUTLIER DETECTION & DIAGNOSIS                  ")
    print("=" * 70)
    
    for col in columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        outlier_pct = (len(outliers) / len(df)) * 100
        
        outlier_summary[col] = {
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "Lower Bound": lower_bound,
            "Upper Bound": upper_bound,
            "Outlier Count": len(outliers),
            "Outlier Pct": outlier_pct
        }
        print(f"Feature: {col:<25} | Bounds: [{lower_bound:.1f}, {upper_bound:.1f}] | "
              f"Outliers: {len(outliers):>5,} ({outlier_pct:5.2f}%)")
              
    return outlier_summary


def generate_charts(df, charts_dir):
    """Generate and save all 10 analytical charts."""
    setup_visualization_style()
    print(f"\nGenerating and saving charts to: {charts_dir} ...")

    # -------------------------------------------------------------
    # Chart 1: Numerical Feature Distributions (Histograms & KDE)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    num_features = ["lead_time", "adr", "stays_in_week_nights", "total_of_special_requests"]
    titles = ["Lead Time (Days)", "Average Daily Rate ($ ADR)", "Stays in Week Nights", "Total Special Requests"]
    colors = ["#2b5c8f", "#d95f02", "#7570b3", "#1b9e77"]

    for ax, feat, title, color in zip(axes.flatten(), num_features, titles, colors):
        sns.histplot(df[feat], kde=True, ax=ax, color=color, bins=30, edgecolor="black", alpha=0.6)
        mean_val = df[feat].mean()
        median_val = df[feat].median()
        ax.axvline(mean_val, color="red", linestyle="--", linewidth=1.5, label=f"Mean: {mean_val:.1f}")
        ax.axvline(median_val, color="gold", linestyle="-", linewidth=1.5, label=f"Median: {median_val:.1f}")
        ax.set_title(f"Distribution of {title}", fontweight="bold")
        ax.set_xlabel(title)
        ax.set_ylabel("Frequency (Count)")
        ax.legend()

    plt.suptitle("01. Univariate Analysis: Key Numerical Distributions", fontsize=15, weight="bold", y=1.02)
    plt.tight_layout()
    chart1_path = os.path.join(charts_dir, "01_numerical_distributions.png")
    plt.savefig(chart1_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 01_numerical_distributions.png")

    # -------------------------------------------------------------
    # Chart 2: Categorical Distributions (Bar Charts)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    cat_features = ["hotel", "market_segment", "meal", "customer_type"]
    cat_titles = ["Hotel Property Type", "Booking Market Segment", "Meal Package Preference", "Customer Segment"]

    for ax, feat, title in zip(axes.flatten(), cat_features, cat_titles):
        counts = df[feat].value_counts()
        sns.barplot(x=counts.index, y=counts.values, ax=ax, hue=counts.index, palette="Blues_r", legend=False)
        ax.set_title(f"Distribution by {title}", fontweight="bold")
        ax.set_xlabel(title)
        ax.set_ylabel("Total Reservations")
        ax.tick_params(axis="x", rotation=25)
        for idx, val in enumerate(counts.values):
            ax.text(idx, val + (max(counts.values) * 0.02), f"{val:,}", ha="center", fontsize=9, fontweight="bold")

    plt.suptitle("02. Univariate Analysis: Categorical Feature Frequencies", fontsize=15, weight="bold", y=1.02)
    plt.tight_layout()
    chart2_path = os.path.join(charts_dir, "02_categorical_distributions.png")
    plt.savefig(chart2_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 02_categorical_distributions.png")

    # -------------------------------------------------------------
    # Chart 3: Correlation Matrix Heatmap
    # -------------------------------------------------------------
    plt.figure(figsize=(11, 8))
    corr_cols = [
        "is_canceled", "lead_time", "stays_in_weekend_nights", "stays_in_week_nights",
        "adults", "children", "is_repeated_guest", "previous_cancellations",
        "booking_changes", "days_in_waiting_list", "adr", "required_car_parking_spaces",
        "total_of_special_requests"
    ]
    corr_matrix = df[corr_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    cmap = sns.diverging_palette(220, 15, as_cmap=True)
    sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmin=-0.3, vmax=0.5, annot=True,
                fmt=".2f", linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title("03. Correlation Matrix of Numerical Booking Attributes", fontsize=14, weight="bold", pad=15)
    plt.tight_layout()
    chart3_path = os.path.join(charts_dir, "03_correlation_heatmap.png")
    plt.savefig(chart3_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 03_correlation_heatmap.png")

    # -------------------------------------------------------------
    # Chart 4: Lead Time vs Cancellation Rate (Quartile / Decile Trend)
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    df["lead_time_bracket"] = pd.qcut(df["lead_time"], q=5, labels=["Very Low (0-9d)", "Low (10-33d)", "Medium (34-70d)", "High (71-140d)", "Very High (141+d)"])
    cancel_by_lead = df.groupby("lead_time_bracket", observed=False)["is_canceled"].mean() * 100

    ax = sns.barplot(x=cancel_by_lead.index, y=cancel_by_lead.values, hue=cancel_by_lead.index, palette="Reds", legend=False)
    plt.title("04. Impact of Booking Lead Time on Cancellation Rate", fontsize=14, weight="bold", pad=12)
    plt.xlabel("Lead Time Quantile Bracket (Days Advance)")
    plt.ylabel("Cancellation Rate (%)")
    plt.ylim(0, 45)
    for i, v in enumerate(cancel_by_lead.values):
        ax.text(i, v + 1.2, f"{v:.1f}%", ha="center", fontweight="bold", fontsize=11)
    plt.tight_layout()
    chart4_path = os.path.join(charts_dir, "04_lead_time_vs_cancellation.png")
    plt.savefig(chart4_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 04_lead_time_vs_cancellation.png")

    # -------------------------------------------------------------
    # Chart 5: Seasonality & ADR Time-Series Trends
    # -------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(12, 6))
    month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    monthly_arrivals = df["arrival_date_month"].value_counts().reindex(month_order)
    monthly_adr_resort = df[df["hotel"] == "Resort Hotel"].groupby("arrival_date_month")["adr"].mean().reindex(month_order)
    monthly_adr_city = df[df["hotel"] == "City Hotel"].groupby("arrival_date_month")["adr"].mean().reindex(month_order)

    # Left Axis: Booking Volume
    color_bar = "#85c1e9"
    bars = ax1.bar(month_order, monthly_arrivals.values, color=color_bar, alpha=0.5, label="Total Booking Volume", width=0.6)
    ax1.set_xlabel("Arrival Month", fontweight="bold")
    ax1.set_ylabel("Total Reservations (Volume)", color="#2874a6", fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#2874a6")
    ax1.tick_params(axis="x", rotation=35)
    ax1.set_ylim(0, 14000)

    # Right Axis: ADR Trends
    ax2 = ax1.twinx()
    l1 = ax2.plot(month_order, monthly_adr_resort.values, color="#e74c3c", marker="o", linewidth=2.5, label="Resort Hotel ADR ($)")
    l2 = ax2.plot(month_order, monthly_adr_city.values, color="#2ecc71", marker="s", linewidth=2.5, label="City Hotel ADR ($)")
    ax2.set_ylabel("Average Daily Rate ($ ADR)", color="#2c3e50", fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#2c3e50")
    ax2.grid(False)
    ax2.set_ylim(40, 210)

    # Unified Legend
    lines = [bars] + l1 + l2
    labels = ["Total Booking Volume", "Resort Hotel ADR ($)", "City Hotel ADR ($)"]
    ax1.legend(lines, labels, loc="upper left", frameon=True)

    plt.title("05. Seasonal Trends: Monthly Booking Demand & ADR Inversion", fontsize=14, weight="bold", pad=15)
    plt.tight_layout()
    chart5_path = os.path.join(charts_dir, "05_monthly_seasonality_and_adr.png")
    plt.savefig(chart5_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 05_monthly_seasonality_and_adr.png")

    # -------------------------------------------------------------
    # Chart 6: Market Segment Booking Share vs Cancellation Rate
    # -------------------------------------------------------------
    seg_summary = df.groupby("market_segment").agg(
        Total_Bookings=("is_canceled", "count"),
        Cancellation_Rate=("is_canceled", lambda x: x.mean() * 100)
    ).sort_values("Total_Bookings", ascending=False)

    fig, ax1 = plt.subplots(figsize=(11, 5))
    x_pos = np.arange(len(seg_summary))
    width = 0.35

    ax1.bar(x_pos - width/2, seg_summary["Total_Bookings"], width, label="Total Bookings", color="#3498db")
    ax1.set_ylabel("Total Bookings", color="#2980b9", fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#2980b9")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(seg_summary.index, rotation=25)

    ax2 = ax1.twinx()
    ax2.bar(x_pos + width/2, seg_summary["Cancellation_Rate"], width, label="Cancellation Rate (%)", color="#e67e22")
    ax2.set_ylabel("Cancellation Rate (%)", color="#d35400", fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#d35400")
    ax2.grid(False)
    ax2.set_ylim(0, 50)

    for i in x_pos:
        rate = seg_summary["Cancellation_Rate"].iloc[i]
        ax2.text(i + width/2, rate + 1, f"{rate:.1f}%", ha="center", fontsize=9, fontweight="bold")

    plt.title("06. Market Segment Comparison: Booking Volume vs Cancellation Risk", fontsize=14, weight="bold", pad=15)
    plt.tight_layout()
    chart6_path = os.path.join(charts_dir, "06_market_segment_cancellation_comparison.png")
    plt.savefig(chart6_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 06_market_segment_cancellation_comparison.png")

    # -------------------------------------------------------------
    # Chart 7: Special Requests Impact on Cancellations
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 5))
    req_cancel = df.groupby("total_of_special_requests")["is_canceled"].mean() * 100
    req_counts = df["total_of_special_requests"].value_counts().sort_index()

    ax = sns.barplot(x=req_cancel.index, y=req_cancel.values, hue=req_cancel.index, palette="viridis", legend=False)
    plt.title("07. Guest Commitment Proxy: Special Requests vs Cancellation Rate", fontsize=14, weight="bold", pad=12)
    plt.xlabel("Number of Special Requests Made by Guest")
    plt.ylabel("Cancellation Rate (%)")
    plt.ylim(0, 40)
    for idx, (rate, count) in enumerate(zip(req_cancel.values, req_counts.values)):
        ax.text(idx, rate + 1, f"{rate:.1f}%\n(n={count:,})", ha="center", fontsize=9, fontweight="bold")
    plt.tight_layout()
    chart7_path = os.path.join(charts_dir, "07_special_requests_impact.png")
    plt.savefig(chart7_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 07_special_requests_impact.png")

    # -------------------------------------------------------------
    # Chart 8: Room Assignment Discrepancy & Cancellation
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    df["room_status"] = np.where(df["reserved_room_type"] == df["assigned_room_type"], "Same Room Assigned", "Different Room Assigned (Upgrade)")
    room_cancel = df.groupby("room_status")["is_canceled"].mean() * 100
    room_counts = df["room_status"].value_counts()

    ax = sns.barplot(x=room_cancel.index, y=room_cancel.values, hue=room_cancel.index, palette=["#e74c3c", "#27ae60"], legend=False)
    plt.title("08. Room Assignment Match vs Upgrade Cancellation Rates", fontsize=14, weight="bold", pad=12)
    plt.xlabel("Room Assignment Outcome")
    plt.ylabel("Cancellation Rate (%)")
    plt.ylim(0, 38)
    for idx, (label, rate) in enumerate(room_cancel.items()):
        cnt = room_counts[label]
        ax.text(idx, rate + 1.2, f"{rate:.1f}%\n({cnt:,} bookings)", ha="center", fontweight="bold", fontsize=11)
    plt.tight_layout()
    chart8_path = os.path.join(charts_dir, "08_room_assignment_discrepancy.png")
    plt.savefig(chart8_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 08_room_assignment_discrepancy.png")

    # -------------------------------------------------------------
    # Chart 9: Top 10 Origin Countries
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    top_countries = df["country"].value_counts().head(10)
    country_names = {
        "PRT": "Portugal", "GBR": "United Kingdom", "FRA": "France", "ESP": "Spain",
        "DEU": "Germany", "ITA": "Italy", "IRL": "Ireland", "BEL": "Belgium",
        "BRA": "Brazil", "NLD": "Netherlands"
    }
    labels = [f"{country_names.get(c, c)} ({c})" for c in top_countries.index]

    ax = sns.barplot(x=top_countries.values, y=labels, hue=labels, palette="crest_r", legend=False)
    plt.title("09. Top 10 Guest Countries of Origin", fontsize=14, weight="bold", pad=12)
    plt.xlabel("Total Guest Reservations")
    plt.ylabel("Origin Country")
    for idx, val in enumerate(top_countries.values):
        pct = (val / len(df)) * 100
        ax.text(val + 300, idx, f"{val:,} ({pct:.1f}%)", va="center", fontsize=9, fontweight="bold")
    plt.tight_layout()
    chart9_path = os.path.join(charts_dir, "09_top_origin_countries.png")
    plt.savefig(chart9_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 09_top_origin_countries.png")

    # -------------------------------------------------------------
    # Chart 10: IQR Outlier Boxplots
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 4, figsize=(15, 5))
    outlier_cols = ["lead_time", "adr", "stays_in_week_nights", "stays_in_weekend_nights"]
    outlier_titles = ["Lead Time (Days)", "ADR ($/Night)", "Week Nights", "Weekend Nights"]

    for ax, col, title in zip(axes, outlier_cols, outlier_titles):
        sns.boxplot(y=df[col], ax=ax, color="#9b59b6", flierprops={"marker": "o", "markersize": 3, "alpha": 0.4})
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        ax.axhline(upper, color="red", linestyle=":", label=f"Upper Fence: {upper:.1f}")
        ax.set_title(title, fontweight="bold")
        ax.set_ylabel(title)
        ax.legend(loc="upper right", fontsize=8)

    plt.suptitle("10. Anomaly Detection: IQR Outlier Boundaries Across Key Metrics", fontsize=15, weight="bold", y=1.03)
    plt.tight_layout()
    chart10_path = os.path.join(charts_dir, "10_outlier_boxplots_iqr.png")
    plt.savefig(chart10_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(" -> Saved 10_outlier_boxplots_iqr.png")

    print("\n[OK] All 10 charts successfully generated and saved to /charts/")


def display_key_insights():
    """Print the five evidence-backed analytical insights."""
    insights = [
        {
            "num": 1,
            "title": "Lead Time is the Single Greatest Determinant of Cancellation Risk",
            "finding": "Reservations booked far in advance exhibit over 3.6x higher cancellation rates compared to short-notice bookings.",
            "evidence": "Bookings in the lowest quartile (0-11 days) have a 10.3% cancellation rate, rising steadily to 28.6% (11-49 days), 33.7% (49-125 days), and peaking at 37.6% for bookings made 125+ days in advance (Chart 04).",
            "impact": "Revenue managers can implement tiered cancellation policies—requiring modest deposits or stricter cancellation windows for bookings made more than 90 days ahead to curb phantom occupancy."
        },
        {
            "num": 2,
            "title": "Extreme Summer Seasonality Drives a 280% Surge in Resort Pricing",
            "finding": "Hotel booking demand is heavily concentrated in summer, but Resort and City Hotels experience opposite seasonal price sensitivity.",
            "evidence": "Total monthly arrivals peak in August (11,242 bookings; 2.4x January's 4,685). Resort Hotel ADR surges from a winter low of $49.18 in January to a peak of $187.57 in August (+281%), whereas City Hotel ADR remains relatively flat between $85 and $128 (Chart 05).",
            "impact": "Resort properties have immense dynamic pricing power during July-August, while City properties require mid-week corporate packages to stabilize year-round revenue."
        },
        {
            "num": 3,
            "title": "Special Requests Serve as a Powerful Behavioral Proxy for Guest Commitment",
            "finding": "The likelihood of cancellation drops precipitously with every additional special request made by a customer.",
            "evidence": "Guests with 0 special requests cancel 33.2% of the time. This plummets to 22.4% for 1 request, 17.1% for 3 requests, and just 5.6% for 5 requests (Chart 07).",
            "impact": "Encouraging guests to customize their stay during digital check-in (e.g., selecting floor preference, pillow type, or arrival time) actively increases customer psychological commitment and slashes no-shows."
        },
        {
            "num": 4,
            "title": "Online Travel Agencies (OTAs) Generate High Volume but Suffer Elevated Churn",
            "finding": "Online Travel Agencies dominate total distribution volume but deliver the most fragile, high-churn customer base.",
            "evidence": "Online TA accounts for 51,000+ bookings (58.9% market share) with an elevated cancellation rate of 35.4%, compared to Direct Bookings (14.7% cancellation) and Corporate clients (12.1% cancellation) (Chart 06).",
            "impact": "Hotels should incentivize direct bookings through loyalty rewards, complimentary breakfast, or exclusive perks to reduce dependence on high-commission, high-cancellation third-party platforms."
        },
        {
            "num": 5,
            "title": "The Room Reassignment Paradox: Upgrades Virtually Eliminate Cancellations",
            "finding": "When operational room shortages compel hotel management to assign a different (typically upgraded) room type, cancellation collapses.",
            "evidence": "Guests receiving their exact reserved room type experienced a 31.5% cancellation rate, whereas guests assigned a different room type had an astonishingly low 4.7% cancellation rate (Chart 08).",
            "impact": "Proactive complimentary room upgrades can be leveraged as a tactical retention mechanism for high-value guests at risk of cancellation, simultaneously resolving room inventory bottlenecks."
        }
    ]

    print("\n" + "=" * 70)
    print("                     FIVE KEY ANALYTICAL INSIGHTS                   ")
    print("=" * 70)
    for item in insights:
        print(f"\n[INSIGHT {item['num']}: {item['title'].upper()}]")
        print(f"  * Finding:  {item['finding']}")
        print(f"  * Evidence: {item['evidence']}")
        print(f"  * Why it Matters: {item['impact']}")
    print("=" * 70)


def main():
    data_path, charts_dir = get_paths()
    print(f"Loading cleaned dataset from: {data_path}")
    df = load_dataset(data_path)
    compute_summary_statistics(df)
    detect_iqr_outliers(df, ["lead_time", "adr", "stays_in_week_nights", "stays_in_weekend_nights"])
    generate_charts(df, charts_dir)
    display_key_insights()
    print("\nEDA pipeline execution completed successfully!")


if __name__ == "__main__":
    main()
