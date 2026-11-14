import pandas as pd
from ingestion import load_datasets


def check_duplicate_identifiers(datasets):

    print("\n========== DUPLICATE IDENTIFIER CHECKS ==========")

    checks = {
        "campaign_spend": ["spend_id"],
        "conversions": ["event_id", "order_id"],
        "touchpoints": ["touchpoint_id"],
        "campaigns": ["campaign_id"]
    }

    for dataset_name, columns in checks.items():

        df = datasets[dataset_name]

        for column in columns:

            duplicates = df[
                df.duplicated(subset=[column], keep=False)
            ]

            print(f"\n{dataset_name} - {column}")

            if duplicates.empty:
                print("No duplicate identifiers found.")
            else:
                print(duplicates.to_string(index=False))


def check_duplicate_spend(datasets):

    print("\n========== POSSIBLE DUPLICATE SPEND ==========")

    df = datasets["campaign_spend"]

    duplicates = df[
        df.duplicated(
            subset=["campaign_id", "spend_date", "spend_amount"],
            keep=False
        )
    ]

    print(duplicates.to_string(index=False))


def check_invalid_timestamps(datasets):

    print("\n========== INVALID TIMESTAMP CHECKS ==========")

    timestamp_columns = {
        "conversions": "conversion_timestamp",
        "touchpoints": "touchpoint_timestamp",
        "campaign_spend": "spend_date",
        "campaigns": "start_date"
    }

    for dataset_name, column in timestamp_columns.items():

        df = datasets[dataset_name]

        parsed_dates = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid = df[parsed_dates.isna()]

        print(f"\n{dataset_name} - {column}")
        print(f"Invalid timestamps: {len(invalid)}")

        if not invalid.empty:
            print(invalid.to_string(index=False))


def check_invalid_numeric_values(datasets):

    print("\n========== NUMERIC VALUE CHECKS ==========")

    conversions = datasets["conversions"]

    invalid_revenue = conversions[
        pd.to_numeric(
            conversions["revenue_amount"],
            errors="coerce"
        ) <= 0
    ]

    print("\nInvalid conversion revenue:")
    print(invalid_revenue.to_string(index=False))

    spend = datasets["campaign_spend"]

    invalid_spend = spend[
        pd.to_numeric(
            spend["spend_amount"],
            errors="coerce"
        ) < 0
    ]

    print("\nNegative campaign spend:")
    print(invalid_spend.to_string(index=False))


def check_missing_values(datasets):

    print("\n========== MISSING VALUE CHECKS ==========")

    for name, df in datasets.items():

        missing = df[df.isnull().any(axis=1)]

        print(f"\n{name}: {len(missing)} rows with missing values")

        if not missing.empty:
            print(missing.to_string(index=False))


def check_channel_variations(datasets):

    print("\n========== CHANNEL VALUE CHECKS ==========")

    touchpoints = datasets["touchpoints"]

    print("\nUnique touchpoint source channels:")

    for channel in sorted(
        touchpoints["source_channel"].dropna().unique()
    ):
        print(repr(channel))


if __name__ == "__main__":

    datasets = load_datasets()

    check_duplicate_identifiers(datasets)

    check_duplicate_spend(datasets)

    check_invalid_timestamps(datasets)

    check_invalid_numeric_values(datasets)

    check_missing_values(datasets)

    check_channel_variations(datasets)

    print("\nAll data-quality checks completed!")