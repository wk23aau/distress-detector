#!/usr/bin/env python3
"""
Feature Extraction Script using BERT Embeddings for Distress Detection

This script loads the processed CSV file (e.g., TrueOffMyChest_cleaned.csv) from the input directory,
uses the "full_text" field (which includes title, flair, and selftext) to generate BERT embeddings,
and engineers additional features (text_length and engagement_score). The final feature matrix is a 
concatenation of BERT embeddings (768 dims) and engineered features (2 dims). The features and labels 
are then saved as NumPy arrays for subsequent model training.

Usage:
    python feature_extraction_bert.py --input_file data/processed/TrueOffMyChest_cleaned.csv --output_dir data/processed/features
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

def generate_bert_embeddings(texts, batch_size=8):
    """
    Generate BERT embeddings for a list of texts using the [CLS] token.
    Processes texts in batches for efficiency.
    """
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating BERT embeddings"):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        # Use the [CLS] token embedding (first token) as the sentence representation
        batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        embeddings.append(batch_embeddings)
    embeddings = np.vstack(embeddings)
    return embeddings

def engineer_features(df):
    """
    Engineer additional features:
      - text_length: number of characters in the full_text.
      - engagement_score: sum of score and number of comments.
    Returns a NumPy array of these engineered features.
    """
    df["text_length"] = df["full_text"].apply(len)
    df["engagement_score"] = df["score"] + df["num_comments"]
    engineered_features = df[["text_length", "engagement_score"]].values
    return engineered_features

def main(input_file, output_dir, batch_size):
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the processed CSV
    df = pd.read_csv(input_file)
    # Ensure full_text exists; if not, combine title and selftext
    if "full_text" not in df.columns:
        df["full_text"] = (df["title"].fillna("") + " " + df["selftext"].fillna("")).str.strip()
    # Filter out posts with empty full_text
    df = df[df["full_text"].str.len() > 0]
    print(f"Loaded {len(df)} posts from {input_file}")
    
    # Generate BERT embeddings for the "full_text" field
    bert_embeddings = generate_bert_embeddings(df["full_text"].tolist(), batch_size=batch_size)
    print(f"BERT embeddings shape: {bert_embeddings.shape}")
    
    # Engineer additional features
    extra_features = engineer_features(df)
    print(f"Engineered features shape: {extra_features.shape}")
    
    # Concatenate BERT embeddings with engineered features along axis=1
    features = np.hstack([bert_embeddings, extra_features])
    print(f"Final feature matrix shape: {features.shape}")
    
    # Save features and labels as NumPy arrays
    features_file = os.path.join(output_dir, "features.npy")
    labels_file = os.path.join(output_dir, "labels.npy")
    np.save(features_file, features)
    np.save(labels_file, df["label"].values)
    print(f"Saved features to {features_file}")
    print(f"Saved labels to {labels_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature extraction with BERT embeddings for distress detection.")
    parser.add_argument("--input_file", type=str, default="data/processed/TrueOffMyChest_cleaned.csv", help="Path to the processed CSV file.")
    parser.add_argument("--output_dir", type=str, default="data/processed/features", help="Directory to save the extracted features and labels.")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for processing texts through BERT.")
    args = parser.parse_args()
    
    main(args.input_file, args.output_dir, args.batch_size)
