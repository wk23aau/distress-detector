#!/usr/bin/env python3
"""
Stratified Data Split Script for Distress Detection

This script loads the processed CSV file (e.g., TrueOffMyChest_cleaned.csv),
splits it into train, validation, and test sets using stratified sampling based on the "label" column,
and saves the resulting datasets as train.csv, val.csv, and test.csv in the specified output directory.

Usage:
    python split_data.py --input_file data/processed/TrueOffMyChest_cleaned.csv --output_dir data/processed --test_size 0.2 --val_size 0.1
"""

import os
import argparse
import pandas as pd
from sklearn.model_selection import train_test_split

def main(input_file, output_dir, test_size, val_size, random_state):
    # Load the processed CSV
    df = pd.read_csv(input_file)
    
    print("Full dataset label distribution:")
    print(df["label"].value_counts())
    
    # First split: train_val and test
    train_val_df, test_df = train_test_split(
        df, test_size=test_size, stratify=df["label"], random_state=random_state
    )
    
    # Now, split train_val into train and validation.
    # The validation set size relative to the entire dataset is val_size.
    # So, the fraction relative to train_val is:
    val_ratio = val_size / (1 - test_size)
    train_df, val_df = train_test_split(
        train_val_df, test_size=val_ratio, stratify=train_val_df["label"], random_state=random_state
    )
    
    print("\nTrain label distribution:")
    print(train_df["label"].value_counts())
    print("\nValidation label distribution:")
    print(val_df["label"].value_counts())
    print("\nTest label distribution:")
    print(test_df["label"].value_counts())
    
    # Save the splits
    os.makedirs(output_dir, exist_ok=True)
    train_path = os.path.join(output_dir, "train.csv")
    val_path = os.path.join(output_dir, "val.csv")
    test_path = os.path.join(output_dir, "test.csv")
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"\nSaved train data to: {train_path}")
    print(f"Saved validation data to: {val_path}")
    print(f"Saved test data to: {test_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stratified splitting for distress detection data")
    parser.add_argument("--input_file", type=str, default="data/processed/TrueOffMyChest_cleaned.csv", help="Path to the processed CSV file.")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Directory to save the split CSV files.")
    parser.add_argument("--test_size", type=float, default=0.2, help="Fraction of data to reserve for the test set (e.g., 0.2 means 20%).")
    parser.add_argument("--val_size", type=float, default=0.1, help="Fraction of data to reserve for the validation set (relative to the entire dataset).")
    parser.add_argument("--random_state", type=int, default=42, help="Random state for reproducibility.")
    args = parser.parse_args()
    
    main(args.input_file, args.output_dir, args.test_size, args.val_size, args.random_state)
