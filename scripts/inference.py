#!/usr/bin/env python3
"""
Inference Script for Distress Detection Using BERT Embeddings and Engineered Features

This script loads a JSON file of new posts from the specified input directory (e.g., data/raw/reddit-posts/prompts),
processes the posts by creating a "full_text" column (concatenating "title" and "selftext" if necessary),
generates BERT embeddings (with batching and truncation), engineers additional features (text_length and engagement_score),
and concatenates them into a final feature matrix. It then loads a pre-trained model (best_model.pth) from the model directory,
runs inference to obtain probability scores and binary predictions, and saves the results to a CSV file.

Usage:
    python inference.py --input_file data/raw/reddit-posts/prompts/confessions_1-100_2025-03-12_01-21-23.json --output_file data/raw/prompts/confessions_predictions.csv --batch_size 8 --model_dir models --features_dim 770
"""

import os
import argparse
import json
import re
import emoji
import pandas as pd
from tqdm import tqdm
import torch
from transformers import BertTokenizer, BertModel
import numpy as np

# Load pre-trained BERT model and tokenizer (using bert-base-uncased)
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model_bert = BertModel.from_pretrained("bert-base-uncased")
model_bert.eval()  # Set to evaluation mode

def clean_text(text):
    """Clean text by converting emojis to text, lowercasing, removing URLs/emails/phone numbers, and normalizing whitespace."""
    if not text:
        return ""
    text = emoji.demojize(text, delimiters=("", ""))
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"\+?\d[\d -]{8,12}\d", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_json_data(input_file):
    """
    Load posts from a JSON file.
    Assumes the JSON file contains a list of posts (dictionaries).
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

def process_dataset_from_json(input_file):
    """
    Load new posts from a JSON file and ensure a "full_text" column exists.
    If "full_text" is not present, it is created by concatenating "title" and "selftext".
    """
    df = load_json_data(input_file)
    for col in ["title", "selftext"]:
        df[col] = df[col].fillna("")
    if "full_text" not in df.columns:
        df["full_text"] = (df["title"] + " " + df["selftext"]).str.strip()
    df = df[df["full_text"].str.len() > 0]
    return df

def generate_bert_embeddings(texts, batch_size=8):
    """
    Generate BERT embeddings for a list of texts using the [CLS] token as the sentence representation.
    Processes texts in batches with truncation (max_length=512).
    Returns a NumPy array of embeddings.
    """
    all_embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating BERT embeddings"):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model_bert(**inputs)
        batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()  # [CLS] token embeddings
        all_embeddings.append(batch_embeddings)
    embeddings = np.vstack(all_embeddings)
    return embeddings

def engineer_features(df):
    """
    Engineer additional features:
      - text_length: number of characters in "full_text"
      - engagement_score: sum of "score" and "num_comments" (if available; else defaults to 0)
    Returns a NumPy array with shape (num_samples, 2).
    """
    df["text_length"] = df["full_text"].apply(len)
    if "score" not in df.columns:
        df["score"] = 0
    if "num_comments" not in df.columns:
        df["num_comments"] = 0
    df["engagement_score"] = df["score"] + df["num_comments"]
    return df[["text_length", "engagement_score"]].values

def load_trained_model(model_dir, input_dim, device):
    """
    Load the trained model from the specified directory.
    Assumes the model was saved as "best_model.pth" and uses the DistressClassifier definition.
    """
    from model_train import DistressClassifier  # Import the classifier definition from model_train.py
    model_path = os.path.join(model_dir, "best_model.pth")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model not found at {model_path}")
    model = DistressClassifier(input_dim=input_dim)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

def main(input_file, output_file, batch_size, model_dir, features_dim):
    # Load and process dataset from JSON
    df = process_dataset_from_json(input_file)
    print(f"Loaded {len(df)} posts from {input_file}")
    
    # Generate BERT embeddings for the "full_text" column
    texts = df["full_text"].tolist()
    bert_embeddings = generate_bert_embeddings(texts, batch_size=batch_size)
    print(f"BERT embeddings shape: {bert_embeddings.shape}")
    
    # Engineer additional features
    extra_features = engineer_features(df)
    print(f"Engineered features shape: {extra_features.shape}")
    
    # Concatenate features to form final feature matrix
    features = np.hstack([bert_embeddings, extra_features])
    print(f"Final feature matrix shape: {features.shape}")
    
    # Load the trained model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_trained_model(model_dir, input_dim=features_dim, device=device)
    
    # Run inference
    model.eval()
    with torch.no_grad():
        features_tensor = torch.tensor(features, dtype=torch.float32).to(device)
        outputs = model(features_tensor).squeeze(1)
        probabilities = torch.sigmoid(outputs).cpu().numpy()
        predictions = (probabilities >= 0.5).astype(int)
    
    # Add predictions and probabilities to the DataFrame and save
    df["predicted_label"] = predictions
    df["probability"] = probabilities
    df.to_csv(output_file, index=False)
    print(f"Saved predictions to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inference for distress detection using BERT embeddings and engineered features from JSON posts.")
    parser.add_argument("--input_file", type=str, default="data/raw/reddit-posts/prompts/confessions_1-100_2025-03-12_01-21-23.json", help="Path to the JSON file containing new posts.")
    parser.add_argument("--output_file", type=str, default="data/processed/reddit-posts/prompts/confessions_predictions.csv", help="Path to save the predictions CSV file.")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for processing texts through BERT.")
    parser.add_argument("--model_dir", type=str, default="models", help="Directory containing the trained model (best_model.pth).")
    parser.add_argument("--features_dim", type=int, default=770, help="Total dimension of features (BERT embeddings + engineered features).")
    args = parser.parse_args()
    
    main(args.input_file, args.output_file, args.batch_size, args.model_dir, args.features_dim)
