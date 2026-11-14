
import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned"
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "validation"

REPORT_PATH.mkdir(parents=True, exist_ok=True)


def load_cleaned_datasets():

    files = {
        "campaigns": "campaigns_cleaned.csv",
        "campaign_spend": "campaign_spend_cleaned.csv",
        "conversions": "conversions_cleaned.csv",
        "touchpoints": "touchpoints_cleaned.csv",
        "channel_mapping": "channel_mapping_cleaned.csv"
    }

    datasets = {}

    for name, filename in files.items():

        datasets[name] = pd.read_csv(
            CLEANED_PATH / filename
        )

    return datasets


def validate_campaign_references(datasets):

    print("\n========== CAMPAIGN REFERENCE CHECKS ==========")

    campaigns = datasets["campaigns"]

    campaign_ids = set(campaigns["campaign_id"].dropna())

    spend = datasets["campaign_spend"]

    invalid_spend = spend[
        ~spend["campaign_id"].isin(campaign_ids)
    ].copy()

    print("\nInvalid campaign references in spend:")
    print(invalid_spend)

    touchpoints = datasets["touchpoints"]

    invalid_touchpoints = touchpoints[
        ~touchpoints["campaign_id"].isin(campaign_ids)
    ].copy()

    print("\nInvalid campaign references in touchpoints:")
    print(invalid_touchpoints)

    return invalid_spend, invalid_touchpoints


def validate_conversion_uniqueness(datasets):

    print("\n========== CONVERSION UNIQUENESS ==========")

    conversions = datasets["conversions"]

    duplicate_events = conversions[
        conversions.duplicated(
            subset=["event_id"],
            keep=False
        )
    ]

    duplicate_orders = conversions[
        conversions.duplicated(
            subset=["order_id"],
            keep=False
        )
    ]

    print("Duplicate event IDs:", len(duplicate_events))
    print("Duplicate order IDs:", len(duplicate_orders))

    return duplicate_events, duplicate_orders


def validate_channel_mapping(datasets):

    print("\n========== CHANNEL MAPPING CHECK ==========")

    touchpoints = datasets["touchpoints"]

    mapping = datasets["channel_mapping"]

    # Normalize both sides consistently
    touchpoint_channels = set(
        touchpoints["source_channel"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
    )

    mapping_channels = set(
        mapping["source_channel"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
    )

    unmapped_channels = touchpoint_channels - mapping_channels

    print("\nUnmapped source channels:")

    if unmapped_channels:
        for channel in sorted(unmapped_channels):
            print(channel)
    else:
        print("All touchpoint channels have mappings.")

    return unmapped_channels


def validate_required_values(datasets):

    print("\n========== REQUIRED VALUE CHECKS ==========")

    checks = {
        "campaigns": ["campaign_id", "budget_amount"],
        "campaign_spend": [
            "spend_id", "campaign_id", "spend_amount"
        ],
        "conversions": [
            "event_id", "order_id", "revenue_amount"
        ],
        "touchpoints": [
            "touchpoint_id", "campaign_id",
            "interaction_type", "touchpoint_timestamp"
        ]
    }

    issues = []

    for dataset_name, columns in checks.items():

        df = datasets[dataset_name]

        for column in columns:

            missing_count = int(df[column].isna().sum())

            print(
                f"{dataset_name}.{column}: "
                f"{missing_count} missing values"
            )

            if missing_count > 0:
                issues.append({
                    "dataset": dataset_name,
                    "column": column,
                    "missing_values": missing_count
                })

    return pd.DataFrame(issues)


def main():

    datasets = load_cleaned_datasets()

    invalid_spend, invalid_touchpoints = (
        validate_campaign_references(datasets)
    )

    duplicate_events, duplicate_orders = (
        validate_conversion_uniqueness(datasets)
    )

    unmapped_channels = validate_channel_mapping(datasets)

    missing_values = validate_required_values(datasets)

    # Save validation outputs
    invalid_spend.to_csv(
        REPORT_PATH / "invalid_spend_campaigns.csv",
        index=False
    )

    invalid_touchpoints.to_csv(
        REPORT_PATH / "invalid_touchpoint_campaigns.csv",
        index=False
    )

    missing_values.to_csv(
        REPORT_PATH / "missing_required_values.csv",
        index=False
    )

    pd.DataFrame({
        "unmapped_channel": sorted(unmapped_channels)
    }).to_csv(
        REPORT_PATH / "unmapped_channels.csv",
        index=False
    )

    print("\n========== VALIDATION SUMMARY ==========")

    print("Invalid spend campaign references:", len(invalid_spend))
    print("Invalid touchpoint campaign references:", len(invalid_touchpoints))
    print("Duplicate conversion events:", len(duplicate_events))
    print("Duplicate conversion orders:", len(duplicate_orders))
    print("Unmapped channels:", len(unmapped_channels))
    print("Missing required values:", len(missing_values))

    print("\nValidation reports saved successfully!")


if __name__ == "__main__":
    main()
