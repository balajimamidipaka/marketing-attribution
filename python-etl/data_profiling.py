import pandas as pd
from pathlib import Path

from ingestion import load_datasets


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "profiling"
)

REPORT_PATH.mkdir(parents=True, exist_ok=True)


def profile_dataset(name, df):

    print("\n" + "=" * 60)
    print(f"DATASET: {name.upper()}")
    print("=" * 60)

    print("\nFirst five records:")
    print(df.head())

    print("\nDataset shape:")
    print(df.shape)

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nDataset information:")
    df.info()

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nUnique values:")
    print(df.nunique())


def generate_reports(datasets):

    summary_records = []
    column_records = []

    for name, df in datasets.items():

        summary_records.append({
            "dataset": name,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "duplicate_rows": int(df.duplicated().sum()),
            "total_missing_cells": int(df.isnull().sum().sum())
        })

        for column in df.columns:

            column_records.append({
                "dataset": name,
                "column_name": column,
                "data_type": str(df[column].dtype),
                "total_records": len(df),
                "missing_values": int(df[column].isnull().sum()),
                "missing_percentage": round(
                    df[column].isnull().mean() * 100, 2
                ),
                "unique_values": int(df[column].nunique()),
                "duplicate_values": int(df[column].duplicated().sum())
            })

    summary_df = pd.DataFrame(summary_records)

    column_df = pd.DataFrame(column_records)

    summary_df.to_csv(
        REPORT_PATH / "dataset_summary.csv",
        index=False
    )

    column_df.to_csv(
        REPORT_PATH / "column_profile.csv",
        index=False
    )

    print("\nProfiling reports generated successfully!")

    print(f"Reports saved in: {REPORT_PATH}")


if __name__ == "__main__":

    datasets = load_datasets()

    for name, df in datasets.items():

        profile_dataset(name, df)

    generate_reports(datasets)