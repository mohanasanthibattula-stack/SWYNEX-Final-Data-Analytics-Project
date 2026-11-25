"""
SWYNEX Technologies - Internship Task: Data Cleaning & Preparation
Script: src/clean_data.py
Description: End-to-end automated pipeline to profile, clean, standardize,
             and export the Hotel Booking Demand dataset.
Author: SWYNEX Data Analytics Intern
"""

import os
import sys
import pandas as pd
import numpy as np


def get_project_paths():
    """Resolve absolute paths for project directories and files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw", "hotel_bookings_raw.csv")
    cleaned_dir = os.path.join(base_dir, "data", "cleaned")
    cleaned_path = os.path.join(cleaned_dir, "cleaned_dataset.csv")
    
    os.makedirs(cleaned_dir, exist_ok=True)
    return raw_path, cleaned_path


def profile_data(df, stage="RAW"):
    """Print an exhaustive, beginner-friendly diagnostic profile of the DataFrame."""
    print(f"\n{'='*30} {stage} DATA PROFILE {'='*30}")
    print(f"Total Rows:     {df.shape[0]:,}")
    print(f"Total Columns:  {df.shape[1]}")
    
    total_nulls = df.isnull().sum().sum()
    null_cols = df.isnull().sum()[df.isnull().sum() > 0]
    print(f"Total Missing Values: {total_nulls:,}")
    if not null_cols.empty:
        print("Missing Values by Column:")
        for col, count in null_cols.items():
            pct = (count / len(df)) * 100
            print(f"  - {col:25}: {count:6,} ({pct:5.2f}%)")
    else:
        print("  - None! (0 missing values)")

    duplicates = df.duplicated().sum()
    print(f"Duplicate Rows: {duplicates:,} ({(duplicates / len(df)) * 100:.2f}%)")
    print(f"Memory Usage:   {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
    print("=" * 76)


def clean_hotel_data(input_path, output_path):
    """
    Execute end-to-end data cleaning workflow:
      1. Load raw data
      2. Profile initial dataset
      3. Drop duplicate records
      4. Handle missing values with domain justifications
      5. Standardize inconsistent categorical values & text
      6. Remove business logic contradictions (0-guest bookings)
      7. Detect and handle statistical outliers
      8. Fix data types (datetime, integer, categorical)
      9. Perform post-cleaning validation
      10. Export cleaned dataset to CSV
    """
    print(f"Loading raw data from: {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw data file not found at: {input_path}")

    df_raw = pd.read_csv(input_path)
    df = df_raw.copy()

    # Step 1: Initial Profiling
    profile_data(df, stage="RAW")

    # Step 2: Handle Duplicate Records
    raw_duplicates = df.duplicated().sum()
    print(f"\n[Step 1/6] Removing duplicate records...")
    df = df.drop_duplicates()
    print(f" -> Removed {raw_duplicates:,} duplicate rows. Remaining rows: {len(df):,}")

    # Step 3: Handle Missing Values with Justification
    print(f"\n[Step 2/6] Handling missing values...")
    # 'company' (94.3% missing): Retaining a column with nearly 95% missing data introduces high sparsity
    # with minimal analytical predictive value. Dropping the column is the standard best practice.
    print(" -> Dropping 'company' column (>94% missing values; adds extreme sparsity).")
    df = df.drop(columns=['company'])

    # 'agent' (~14% missing): Missing agent ID indicates direct bookings by individual customers
    # without a third-party agency. Imputing with 0 preserves these valid direct transactions.
    print(" -> Imputing 'agent' missing values with 0 (indicates direct customer booking without travel agent).")
    df['agent'] = df['agent'].fillna(0)

    # 'country' (~0.4% missing): Missing country ISO codes. Imputing with 'Unknown' preserves records
    # without fabricating geographical origin assumptions.
    print(" -> Imputing 'country' missing values with 'Unknown'.")
    df['country'] = df['country'].fillna('Unknown')

    # 'children' (4 missing values): Extremely negligible (<0.01%). Imputing with mode/median (0).
    print(" -> Imputing 'children' missing values with 0 (mode/median representing no children).")
    df['children'] = df['children'].fillna(0)

    # Step 4: Standardize Inconsistent Values & Text
    print(f"\n[Step 3/6] Standardizing text and categorical inconsistencies...")
    # Strip leading/trailing whitespaces on all string columns
    str_cols = df.select_dtypes(include='object').columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    # 'meal': 'Undefined' in research dataset documentation equals 'SC' (Self-Catering / No Meal)
    undefined_meals = (df['meal'] == 'Undefined').sum()
    df['meal'] = df['meal'].replace({'Undefined': 'SC'})
    print(f" -> Standardized 'meal' column: mapped {undefined_meals:,} 'Undefined' entries to 'SC' (Self-Catering).")

    # 'market_segment' and 'distribution_channel': Replace rare 'Undefined' values with mode
    mode_market = df['market_segment'].mode()[0]
    mode_dist = df['distribution_channel'].mode()[0]
    df['market_segment'] = df['market_segment'].replace({'Undefined': mode_market})
    df['distribution_channel'] = df['distribution_channel'].replace({'Undefined': mode_dist})
    print(f" -> Imputed 'Undefined' values in 'market_segment' with mode ('{mode_market}') and 'distribution_channel' with mode ('{mode_dist}').")

    # Step 5: Remove Business Logic Contradictions (Invalid Bookings)
    print(f"\n[Step 4/6] Filtering invalid reservations...")
    # A hotel reservation cannot have 0 total guests (0 adults, 0 children, 0 babies)
    zero_guests_mask = (df['adults'] == 0) & (df['children'] == 0) & (df['babies'] == 0)
    zero_guests_count = zero_guests_mask.sum()
    df = df[~zero_guests_mask]
    print(f" -> Filtered out {zero_guests_count:,} invalid rows with 0 total guests (adults=0, children=0, babies=0).")

    # Step 6: Outlier Detection and Handling
    print(f"\n[Step 5/6] Checking and treating statistical outliers...")
    # Average Daily Rate (adr):
    # - Negative price is an impossible billing error
    # - Extreme price of $5,400.00 is a single anomalous data entry error (99.9% of rooms are under $500)
    outlier_adr_neg = (df['adr'] < 0).sum()
    outlier_adr_high = (df['adr'] > 1000).sum()
    df = df[(df['adr'] >= 0) & (df['adr'] <= 1000)]
    print(f" -> Handled 'adr' outliers: removed {outlier_adr_neg} negative rate(s) and {outlier_adr_high} extreme anomaly (> $1,000/night).")

    # Adults count:
    # Records with 20 to 55 adults in a single hotel room are unrealistic operational errors
    outlier_adults = (df['adults'] > 10).sum()
    df = df[df['adults'] <= 10]
    print(f" -> Handled 'adults' outliers: removed {outlier_adults} rows with unrealistic occupancy (>10 adults in a room).")

    # Step 7: Fix Data Types
    print(f"\n[Step 6/6] Converting and correcting data types...")
    # Date conversion
    df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'], format='%Y-%m-%d', errors='coerce')
    
    # Numeric conversions (float -> int)
    df['children'] = df['children'].astype(int)
    df['agent'] = df['agent'].astype(int)

    # Categorical conversions for memory optimization and querying efficiency
    categorical_columns = [
        'hotel', 'meal', 'country', 'market_segment', 'distribution_channel',
        'reserved_room_type', 'assigned_room_type', 'deposit_type',
        'customer_type', 'reservation_status'
    ]
    for col in categorical_columns:
        df[col] = df[col].astype('category')

    # Final deduplication sweep to ensure 0 duplicates post-column pruning
    post_dedup = df.duplicated().sum()
    if post_dedup > 0:
        df = df.drop_duplicates()
        print(f" -> Dropped {post_dedup} post-pruning duplicate rows.")

    # Profile Cleaned Dataset
    profile_data(df, stage="CLEANED")

    # Save to CSV
    print(f"\nExporting cleaned dataset to: {output_path}")
    df.to_csv(output_path, index=False)
    file_size_mb = os.path.getsize(output_path) / (1024**2)
    print(f"SUCCESS: Cleaned dataset saved ({file_size_mb:.2f} MB)")

    # Print Before vs After Comparison Summary Table
    print("\n" + "="*70)
    print("                  BEFORE vs AFTER CLEANING SUMMARY                 ")
    print("="*70)
    print(f"{'Metric':<30} | {'Before (Raw)':<16} | {'After (Cleaned)':<16}")
    print("-"*70)
    print(f"{'Total Records (Rows)':<30} | {df_raw.shape[0]:<16,} | {df.shape[0]:<16,}")
    print(f"{'Total Features (Columns)':<30} | {df_raw.shape[1]:<16} | {df.shape[1]:<16}")
    print(f"{'Missing Values (Nulls)':<30} | {df_raw.isnull().sum().sum():<16,} | {df.isnull().sum().sum():<16}")
    print(f"{'Duplicate Records':<30} | {df_raw.duplicated().sum():<16,} | {df.duplicated().sum():<16}")
    print(f"{'Memory Usage (MB)':<30} | {df_raw.memory_usage(deep=True).sum() / (1024**2):<16.2f} | {df.memory_usage(deep=True).sum() / (1024**2):<16.2f}")
    print("="*70)

    return df


if __name__ == "__main__":
    raw_csv, clean_csv = get_project_paths()
    clean_hotel_data(raw_csv, clean_csv)
