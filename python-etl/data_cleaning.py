
import pandas as pd
from pathlib import Path

from ingestion import load_datasets


# ------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned"
REJECTED_PATH = PROJECT_ROOT / "data" / "rejected"
REVIEW_PATH = PROJECT_ROOT / "data" / "review"

for folder in [CLEANED_PATH, REJECTED_PATH, REVIEW_PATH]:
    folder.mkdir(parents=True, exist_ok=True)


def save_dataframe(df, folder, filename):
    df.to_csv(folder / filename, index=False)


# ------------------------------------------------
# 1. CLEAN CAMPAIGNS
# ------------------------------------------------

def clean_campaigns(df):

    df = df.copy()

    df = df.drop_duplicates(
        subset=["campaign_id"],
        keep="first"
    )

    for column in ["campaign_name", "source_platform", "channel"]:
        df[column] = df[column].astype("string").str.strip()

    df["start_date"] = pd.to_datetime(
        df["start_date"], errors="coerce"
    )

    df["end_date"] = pd.to_datetime(
        df["end_date"], errors="coerce"
    )

    df["budget_amount"] = pd.to_numeric(
        df["budget_amount"], errors="coerce"
    )

    df["budget_currency"] = (
        df["budget_currency"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["campaign_status"] = (
        df["campaign_status"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    return df


# ------------------------------------------------
# 2. CLEAN CAMPAIGN SPEND
# ------------------------------------------------

def clean_campaign_spend(df):

    df = df.copy()

    df["spend_amount"] = pd.to_numeric(
        df["spend_amount"], errors="coerce"
    )

    df["spend_date"] = pd.to_datetime(
        df["spend_date"], errors="coerce"
    )

    df["currency"] = (
        df["currency"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["source_platform"] = (
        df["source_platform"]
        .astype("string")
        .str.strip()
    )

    # Identify invalid spend records
    invalid_mask = (
        df["spend_amount"].isna()
        | (df["spend_amount"] < 0)
        | df["spend_date"].isna()
    )

    rejected = df[invalid_mask].copy()

    rejected["rejection_reason"] = (
        "Missing or invalid spend/date"
    )

    valid = df[~invalid_mask].copy()

    # Identify suspected duplicate spend
    duplicate_mask = valid.duplicated(
        subset=[
            "campaign_id",
            "spend_date",
            "spend_amount",
            "currency",
            "source_platform"
        ],
        keep="first"
    )

    review = valid[duplicate_mask].copy()

    review["review_reason"] = (
        "Possible duplicate spend record"
    )

    # Exclude suspected duplicates from the
    # current analytical dataset pending review
    valid = valid[~duplicate_mask].copy()

    return valid, rejected, review


# ------------------------------------------------
# 3. CLEAN CONVERSIONS
# ------------------------------------------------

def clean_conversions(df):

    df = df.copy()

    df["conversion_timestamp"] = pd.to_datetime(
        df["conversion_timestamp"], errors="coerce"
    )

    df["revenue_amount"] = pd.to_numeric(
        df["revenue_amount"], errors="coerce"
    )

    df["currency"] = (
        df["currency"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["conversion_source"] = (
        df["conversion_source"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------
    # STEP 1: REJECT INVALID CONVERSIONS
    # --------------------------------------------

    invalid_mask = (
        df["conversion_timestamp"].isna()
        | df["revenue_amount"].isna()
        | (df["revenue_amount"] <= 0)
        | df["order_id"].isna()
    )

    rejected = df[invalid_mask].copy()

    rejected["rejection_reason"] = (
        "Invalid timestamp, revenue or order ID"
    )

    valid = df[~invalid_mask].copy()

    # --------------------------------------------
    # STEP 2: IDENTIFY DUPLICATE EVENT IDs
    # --------------------------------------------

    duplicate_events = valid[
        valid.duplicated(
            subset=["event_id"],
            keep="first"
        )
    ].copy()

    duplicate_events["rejection_reason"] = (
        "Duplicate event ID"
    )

    # Remove duplicate event IDs from clean data
    valid = valid.drop_duplicates(
        subset=["event_id"],
        keep="first"
    )

    # --------------------------------------------
    # STEP 3: IDENTIFY DUPLICATE ORDER IDs
    # --------------------------------------------

    valid = valid.sort_values(
        by=["conversion_timestamp", "event_id"]
    )

    duplicate_orders = valid[
        valid.duplicated(
            subset=["order_id"],
            keep="first"
        )
    ].copy()

    duplicate_orders["rejection_reason"] = (
        "Duplicate order ID - earliest valid event retained"
    )

    valid = valid.drop_duplicates(
        subset=["order_id"],
        keep="first"
    )

    # --------------------------------------------
    # STEP 4: HANDLE UNKNOWN CUSTOMER IDENTITIES
    # --------------------------------------------

    valid["identity_status"] = valid["user_id"].apply(
        lambda x: (
            "UNKNOWN"
            if pd.isna(x) or str(x).strip() == ""
            else "KNOWN"
        )
    )

    return (
        valid,
        rejected,
        duplicate_orders,
        duplicate_events
    )


# ------------------------------------------------
# 4. CLEAN TOUCHPOINTS
# ------------------------------------------------

def clean_touchpoints(df):

    df = df.copy()

    df["touchpoint_timestamp"] = pd.to_datetime(
        df["touchpoint_timestamp"], errors="coerce"
    )

    df["source_channel"] = (
        df["source_channel"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    df["interaction_type"] = (
        df["interaction_type"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["device_type"] = (
        df["device_type"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    invalid_mask = (
        df["touchpoint_id"].isna()
        | df["campaign_id"].isna()
        | df["touchpoint_timestamp"].isna()
    )

    rejected = df[invalid_mask].copy()

    rejected["rejection_reason"] = (
        "Missing touchpoint/campaign ID or invalid timestamp"
    )

    valid = df[~invalid_mask].copy()

    # Remove duplicate touchpoint IDs
    valid = valid.drop_duplicates(
        subset=["touchpoint_id"],
        keep="first"
    )

    # Preserve known and anonymous identities
    valid["identity_status"] = valid.apply(
        lambda row: (
            "KNOWN"
            if pd.notna(row["user_id"])
            and str(row["user_id"]).strip() != ""
            else (
                "ANONYMOUS"
                if pd.notna(row["anonymous_id"])
                and str(row["anonymous_id"]).strip() != ""
                else "UNKNOWN"
            )
        ),
        axis=1
    )

    return valid, rejected


# ------------------------------------------------
# 5. CLEAN CHANNEL MAPPING
# ------------------------------------------------

def clean_channel_mapping(df):

    df = df.copy()

    for column in [
        "source_channel",
        "standard_channel",
        "source_platform"
    ]:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # Standardize source channel matching keys
    df["source_channel"] = (
        df["source_channel"].str.lower()
    )

    df = df.drop_duplicates(
        subset=["source_channel"],
        keep="first"
    )

    return df


# ------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------

if __name__ == "__main__":

    datasets = load_datasets()

    print("\nStarting data cleaning...\n")

    # Clean campaigns
    campaigns = clean_campaigns(
        datasets["campaigns"]
    )

    # Clean campaign spend
    (
        spend,
        rejected_spend,
        review_spend
    ) = clean_campaign_spend(
        datasets["campaign_spend"]
    )

    # Clean conversions
    (
        conversions,
        rejected_conversions,
        duplicate_orders,
        duplicate_events
    ) = clean_conversions(
        datasets["conversions"]
    )

    # Clean touchpoints
    (
        touchpoints,
        rejected_touchpoints
    ) = clean_touchpoints(
        datasets["touchpoints"]
    )

    # Clean channel mapping
    channel_mapping = clean_channel_mapping(
        datasets["channel_mapping"]
    )

    # --------------------------------------------
    # SAVE CLEANED DATASETS
    # --------------------------------------------

    save_dataframe(
        campaigns,
        CLEANED_PATH,
        "campaigns_cleaned.csv"
    )

    save_dataframe(
        spend,
        CLEANED_PATH,
        "campaign_spend_cleaned.csv"
    )

    save_dataframe(
        conversions,
        CLEANED_PATH,
        "conversions_cleaned.csv"
    )

    save_dataframe(
        touchpoints,
        CLEANED_PATH,
        "touchpoints_cleaned.csv"
    )

    save_dataframe(
        channel_mapping,
        CLEANED_PATH,
        "channel_mapping_cleaned.csv"
    )

    # --------------------------------------------
    # SAVE REJECTED RECORDS
    # --------------------------------------------

    save_dataframe(
        rejected_spend,
        REJECTED_PATH,
        "campaign_spend_rejected.csv"
    )

    save_dataframe(
        rejected_conversions,
        REJECTED_PATH,
        "conversions_rejected.csv"
    )

    save_dataframe(
        duplicate_orders,
        REJECTED_PATH,
        "duplicate_orders.csv"
    )

    save_dataframe(
        duplicate_events,
        REJECTED_PATH,
        "duplicate_events.csv"
    )

    save_dataframe(
        rejected_touchpoints,
        REJECTED_PATH,
        "touchpoints_rejected.csv"
    )

    # --------------------------------------------
    # SAVE REVIEW RECORDS
    # --------------------------------------------

    save_dataframe(
        review_spend,
        REVIEW_PATH,
        "campaign_spend_review.csv"
    )

    # --------------------------------------------
    # PRINT CLEANING SUMMARY
    # --------------------------------------------

    print("\n========== CLEANING SUMMARY ==========")

    print("Campaigns:", len(campaigns))

    print("Campaign spend:", len(spend))
    print("Rejected spend:", len(rejected_spend))
    print("Spend records for review:", len(review_spend))

    print("Conversions:", len(conversions))
    print("Rejected conversions:", len(rejected_conversions))
    print("Duplicate events:", len(duplicate_events))
    print("Duplicate orders:", len(duplicate_orders))

    print("Touchpoints:", len(touchpoints))
    print("Rejected touchpoints:", len(rejected_touchpoints))

    print("Channel mappings:", len(channel_mapping))

    # --------------------------------------------
    # RECONCILIATION CHECKS
    # --------------------------------------------

    assert (
        len(datasets["campaign_spend"])
        == len(spend) + len(rejected_spend) + len(review_spend)
    ), "Campaign spend record count mismatch"

    assert (
        len(datasets["conversions"])
        == len(conversions)
        + len(rejected_conversions)
        + len(duplicate_events)
        + len(duplicate_orders)
    ), "Conversion record count mismatch"

    assert (
        len(datasets["touchpoints"])
        == len(touchpoints) + len(rejected_touchpoints) + 1
    ), "Touchpoint record count mismatch"

    print("\nReconciliation checks passed!")
    print("Data cleaning completed successfully!")
