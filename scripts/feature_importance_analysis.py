import pandas as pd
from sklearn.feature_selection import VarianceThreshold

# Script Name: feature_selection.py
df = pd.read_csv("data/processed/TrueOffMyChest_1-100_2025-03-10_20-43-05.csv")

# 1. Handle Missing Values
print("Missing values before processing:")
print(df.isnull().sum())

# Fill empty selftext with empty string
df["selftext"] = df["selftext"].fillna("")

# 2. Drop Features with All Missing Values
df = df.drop(columns=["author_flair"])  # 100% missing in your dataset

# 3. Drop Low-Variance Features
selector = VarianceThreshold(threshold=0.05)
df_numeric = df.select_dtypes(include=["number"])
selector.fit(df_numeric)

low_variance_cols = df_numeric.columns[~selector.get_support()].tolist()
print(f"Dropping low-variance features: {low_variance_cols}")

df = df.drop(columns=low_variance_cols)

# Save cleaned dataset
df.to_csv("data/processed/TrueOffMyChest_cleaned.csv", index=False)
print("Cleaned dataset saved with shape:", df.shape)