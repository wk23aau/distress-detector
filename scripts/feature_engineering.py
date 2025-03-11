#!/usr/bin/env python3
"""
Feature Extraction Script using BERT Embeddings for Multimodal Distress Detection

This script performs the following:
1. Loads processed CSV files (e.g., train.csv, val.csv, test.csv) from the input directory.
2. Ensures a combined text field ("full_text") is present (concatenating title and selftext).
3. Generates BERT embeddings for the full_text of each post using a pre-trained BERT model.
4. Engineers additional features (such as text length and engagement score).
5. Concatenates the BERT embeddings and the engineered features to create a final feature matrix.
6. Saves the feature matrix and corresponding labels as NumPy arrays for model training.
"""

import os
import pandas as pd
from tqdm import tqdm
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import argparse

# Load pre-trained BERT model and tokenizer (using BERT-base uncased)
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()  # Set model to evaluation mode

def generate_bert_embeddings(texts):
    """
    Generate BERT embeddings for a list of texts.
    Uses the [CLS] token's embedding as a sentence representation.
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
            # Extract the [CLS] token's embedding (shape: [1, 768])
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            embeddings.append(cls_embedding.squeeze().numpy())
    return np.array(embeddings)

def engineer_features(df):
    """
    Engineer additional features from the DataFrame.
      - text_length: the number of characters in the full_text.
      - engagement_score: a simple sum of score and num_comments.
    Returns a NumPy array of engineered features.
    """
    # Ensure full_text exists
    if "full_text" not in df.columns:
        df["full_text"] = df["title"].fillna("") + " " + df["selftext"].fillna("")
    df["text_length"] = df["full_text"].apply(len)
    df["engagement_score"] = df["score"] + df["num_comments"]
    # You may add additional engineered features here if desired
    engineered = df[["text_length", "engagement_score"]].values
    return engineered

def main(input_dir, output_dir, datasets):
    os.makedirs(output_dir, exist_ok=True)
    
    for dataset in datasets:
        input_path = os.path.join(input_dir, f"{dataset}.csv")
        if not os.path.exists(input_path):
            print(f"File {input_path} not found, skipping.")
            continue
        
        print(f"Processing {input_path}...")
        df = pd.read_csv(input_path)
        
        # Create a combined full_text field
        df["full_text"] = df["title"].fillna("") + " " + df["selftext"].fillna("")
        # Filter out any posts with no content
        df = df[df["full_text"].str.len() > 0]
        print(f"Found {len(df)} posts in {dataset}.csv")
        
        # Generate BERT embeddings for each post's full_text
        bert_embeds = generate_bert_embeddings(df["full_text"].tolist())
        print(f"BERT embeddings shape: {bert_embeds.shape}")
        
        # Engineer additional features from the dataset
        extra_features = engineer_features(df)
        print(f"Engineered features shape: {extra_features.shape}")
        
        # Combine BERT embeddings and engineered features (concatenate along axis=1)
        combined_features = np.hstack([bert_embeds, extra_features])
        print(f"Final feature matrix shape: {combined_features.shape}")
        
        # Save features and labels to output directory
        features_filename = os.path.join(output_dir, f"{dataset}_features.npy")
        labels_filename = os.path.join(output_dir, f"{dataset}_labels.npy")
        np.save(features_filename, combined_features)
        np.save(labels_filename, df["label"].values)
        print(f"Saved features to {features_filename}")
        print(f"Saved labels to {labels_filename}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature extraction with BERT embeddings and engineered features for distress detection.")
    parser.add_argument("--input_dir", type=str, default="data/processed", help="Directory containing processed CSV files (e.g., train.csv, val.csv, test.csv).")
    parser.add_argument("--output_dir", type=str, default="data/processed/features", help="Directory to save the extracted feature matrices and labels.")
    parser.add_argument("--datasets", type=str, nargs="+", default=["train", "val", "test"], help="List of dataset names to process (without file extension).")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir, args.datasets)
