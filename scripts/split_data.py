import pandas as pd
from sklearn.model_selection import train_test_split
import os

# Configuration
INPUT_PATH = "data/processed/TrueOffMyChest_cleaned.csv"
OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load consolidated dataset
df = pd.read_csv(INPUT_PATH)

# Split into train (80%), validation (10%), test (10%)
train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df["label"], random_state=42)

# Save splits
train_df.to_csv(f"{OUTPUT_DIR}/train.csv", index=False)
val_df.to_csv(f"{OUTPUT_DIR}/val.csv", index=False)
test_df.to_csv(f"{OUTPUT_DIR}/test.csv", index=False)

print(f"✅ Split complete: Train ({len(train_df)}), Val ({len(val_df)}), Test ({len(test_df)})")
print("Label distribution in train set:")
print(train_df["label"].value_counts())

# verify columns afterwards
# print("Train set columns:", pd.read_csv("data/processed/train.csv").columns.tolist())