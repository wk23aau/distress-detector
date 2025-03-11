#!/usr/bin/env python3
"""
Feature Extraction Script using BERT Embeddings for Distress Detection

This script performs the following:
1. Loads processed CSV files (train.csv, val.csv, test.csv) from the input directory.
2. Uses the "full_text" column (if available) for generating embeddings.
3. Generates BERT embeddings for each post's full_text using a pre-trained BERT model.
4. Engineers additional features (such as text length and engagement score).
5. Concatenates BERT embeddings with engineered features to form the final feature matrix.
6. Saves the feature matrix and corresponding labels as NumPy arrays for downstream training.
"""

import os
import argparse
import pandas as pd
from tqdm import tqdm
import torch
from transformers import BertTokenizer, BertModel
import numpy as np

# Load pre-trained BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()  # Set model to evaluation mode

def generate_bert_embeddings(texts):
    """
    Generate BERT embeddings for a list of texts using the [CLS] token as the sentence representation.
    """
    embeddings = []
    with torch.no_grad():
        for text in tqdm(texts, desc="Generating BERT embeddings"):
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            outputs = model(**inputs)
            cls_embedding = outputs.last_hidden_state[:, 0, :]  # shape: [1, 768]
            embeddings.append(cls_embedding.squeeze().numpy())
    return np.array(embeddings)

def engineer_features(df):
    """
    Engineer additional features from the DataFrame:
      - text_length: number of characters in full_text.
      - engagement_score: sum of score and number of comments.
    Returns a NumPy array of engineered features.
    """
    df["text_length"] = df["full_text"].apply(len)
    df["engagement_score"] = df["score"] + df["num_comments"]
    return df[["text_length", "engagement_score"]].values

def process_dataset(input_file):
    """
    Load a processed CSV file. Assumes the CSV already contains a "full_text" column.
    If not, it falls back to combining "title" and "selftext".
    Filters out posts with empty full_text.
    """
    df = pd.read_csv(input_file)
    if "full_text" not in df.columns:
        df["full_text"] = (df["title"].fillna("") + " " + df["selftext"].fillna("")).str.strip()
    df = df[df["full_text"].str.len() > 0]
    return df

def main(input_dir, output_dir, datasets):
    os.makedirs(output_dir, exist_ok=True)
    
    for dataset in datasets:
        input_path = os.path.join(input_dir, f"{dataset}.csv")
        if not os.path.exists(input_path):
            print(f"File {input_path} not found. Skipping {dataset}.")
            continue
        
        print(f"Processing {input_path}...")
        df = process_dataset(input_path)
        print(f"Found {len(df)} posts in {dataset}.csv")
        
        # Generate BERT embeddings using the "full_text" column
        bert_embeddings = generate_bert_embeddings(df["full_text"].tolist())
        print(f"BERT embeddings shape: {bert_embeddings.shape}")
        
        # Engineer additional features
        extra_features = engineer_features(df)
        print(f"Engineered features shape: {extra_features.shape}")
        
        # Concatenate BERT embeddings with engineered features
        combined_features = np.hstack([bert_embeddings, extra_features])
        print(f"Final feature matrix shape: {combined_features.shape}")
        
        # Save features and labels as NumPy arrays
        features_filename = os.path.join(output_dir, f"{dataset}_features.npy")
        labels_filename = os.path.join(output_dir, f"{dataset}_labels.npy")
        np.save(features_filename, combined_features)
        np.save(labels_filename, df["label"].values)
        print(f"Saved features to {features_filename}")
        print(f"Saved labels to {labels_filename}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature extraction with BERT embeddings for distress detection.")
    parser.add_argument("--input_dir", type=str, default="data/processed", help="Directory containing processed CSV files.")
    parser.add_argument("--output_dir", type=str, default="data/processed/features", help="Directory to save the extracted feature matrices and labels.")
    parser.add_argument("--datasets", type=str, nargs="+", default=["train", "val", "test"], help="List of dataset names to process (without file extension).")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir, args.datasets)
