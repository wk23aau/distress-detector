#!/usr/bin/env python3
"""
Feature Extraction Script Using BERT Embeddings for Distress Detection

This script loads an auto-labeled CSV file (e.g., TrueOffMyChest_auto_labeled.csv) from the input directory,
uses the "full_text" column to generate BERT embeddings (using batching and truncation to max 512 tokens),
and engineers additional features (text length and engagement score). The final feature matrix is a concatenation
of the 768-dimensional BERT embeddings and the engineered features (2 dimensions), resulting in a 770-dim vector per post.
The script then saves the features and labels as NumPy arrays for downstream model training.

Usage:
    python feature_extraction_bert.py --input_file data/processed/TrueOffMyChest_auto_labeled.csv --output_dir data/processed/features --batch_size 8
"""

import os
import argparse
import pandas as pd
from tqdm import tqdm
import torch
from transformers import BertTokenizer, BertModel
import numpy as np

# Load pre-trained BERT model and tokenizer (using bert-base-uncased)
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()  # set the model to evaluation mode

def generate_bert_embeddings(texts, batch_size=8):
    """
    Generate BERT embeddings for a list of texts using the [CLS] token as the sentence representation.
    Processes texts in batches, applying truncation to a maximum length of 512 tokens.
    Returns a NumPy array of embeddings.
    """
    all_embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating BERT embeddings"):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        # Extract the [CLS] token embedding (index 0) from each sequence
        batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        all_embeddings.append(batch_embeddings)
    embeddings = np.vstack(all_embeddings)
    return embeddings

def engineer_features(df):
    """
    Engineer additional features from the DataFrame:
      - text_length: Number of characters in "full_text".
      - engagement_score: Sum of "score" and "num_comments".
    Returns a NumPy array of shape (num_samples, 2).
    """
    df["text_length"] = df["full_text"].apply(len)
    df["engagement_score"] = df["score"] + df["num_comments"]
    return df[["text_length", "engagement_score"]].values

def process_dataset(input_file):
    """
    Load the auto-labeled CSV file.
    If "full_text" does not exist, create it by concatenating "title" and "selftext".
    Filter out any posts with empty "full_text".
    """
    df = pd.read_csv(input_file)
    if "full_text" not in df.columns:
        df["full_text"] = (df["title"].fillna("") + " " + df["selftext"].fillna("")).str.strip()
    df = df[df["full_text"].str.len() > 0]
    return df

def main(input_file, output_dir, batch_size):
    os.makedirs(output_dir, exist_ok=True)
    
    # Load processed auto-labeled data
    df = process_dataset(input_file)
    print(f"Loaded {len(df)} posts from {input_file}")
    
    # Generate BERT embeddings for the "full_text" column
    bert_embeddings = generate_bert_embeddings(df["full_text"].tolist(), batch_size=batch_size)
    print(f"BERT embeddings shape: {bert_embeddings.shape}")
    
    # Engineer additional features
    extra_features = engineer_features(df)
    print(f"Engineered features shape: {extra_features.shape}")
    
    # Concatenate BERT embeddings with engineered features
    features = np.hstack([bert_embeddings, extra_features])
    print(f"Final feature matrix shape: {features.shape}")
    
    # Save features and labels as NumPy arrays
    features_file = os.path.join(output_dir, "features.npy")
    labels_file = os.path.join(output_dir, "labels.npy")
    np.save(features_file, features)
    np.save(labels_file, df["auto_label"].values)
    print(f"Saved features to {features_file}")
    print(f"Saved labels to {labels_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature extraction with BERT embeddings for distress detection.")
    parser.add_argument("--input_file", type=str, default="data/processed/TrueOffMyChest_auto_labeled.csv", help="Path to the auto-labeled CSV file.")
    parser.add_argument("--output_dir", type=str, default="data/processed/features", help="Directory to save the extracted features and labels.")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for processing texts through BERT.")
    args = parser.parse_args()
    
    main(args.input_file, args.output_dir, args.batch_size)
