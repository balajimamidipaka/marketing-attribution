import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"


def load_datasets():

    datasets = {
        "campaigns": "campaigns.csv",
        "campaign_spend": "campaign_spend.csv",
        "conversions": "conversions.csv",
        "touchpoints": "touchpoints.csv",
        "channel_mapping": "channel_mapping.csv"
    }

    dataframes = {}

    for dataset_name, filename in datasets.items():

        file_path = RAW_DATA_PATH / filename

        try:
            df = pd.read_csv(file_path)

            dataframes[dataset_name] = df

            print(f"\nSuccessfully loaded: {filename}")
            print(f"Number of records: {len(df)}")

        except FileNotFoundError:
            print(f"\nFile not found: {file_path}")
            raise

        except Exception as error:
            print(f"\nError loading {filename}: {error}")
            raise

    return dataframes


if __name__ == "__main__":

    datasets = load_datasets()

    print("\nAll datasets loaded successfully!")