import os
import glob
import pandas as pd
import json

# Configuration
DATA_DIR = "data/raw/"
COMBINED_CSV = "data/combined/combined_posts.csv"
COMBINED_JSON = "data/combined/combined_posts.json"

def combine_csv_files():
    """Combine all CSV files into a single CSV"""
    # Create directory if not exists
    os.makedirs(os.path.dirname(COMBINED_CSV), exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        print("No CSV files found to combine")
        return
    
    # Read and combine CSV files
    combined_df = pd.concat(
        [pd.read_csv(f, low_memory=False) for f in csv_files],
        ignore_index=True
    )
    
    # Save combined CSV
    combined_df.to_csv(COMBINED_CSV, index=False)
    print(f"Combined {len(csv_files)} CSV files into {COMBINED_CSV}")

def combine_json_files():
    """Combine all JSON files into a single JSON"""
    # Create directory if not exists
    os.makedirs(os.path.dirname(COMBINED_JSON), exist_ok=True)
    
    # Find all JSON files
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    if not json_files:
        print("No JSON files found to combine")
        return
    
    # Read and combine JSON files
    combined_data = []
    for file in json_files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
                combined_data.extend(data)
        except Exception as e:
            print(f"Error reading {file}: {str(e)}")
    
    # Save combined JSON
    with open(COMBINED_JSON, "w") as f:
        json.dump(combined_data, f, indent=2)
    print(f"Combined {len(json_files)} JSON files into {COMBINED_JSON}")

if __name__ == "__main__":
    print("Starting data combination process...")
    
    # Combine CSV files
    combine_csv_files()
    
    # Combine JSON files
    combine_json_files()
    
    print("Combination process completed successfully")