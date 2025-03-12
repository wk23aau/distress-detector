#!/usr/bin/env python3
"""
Baseline Training Script for Distress Detection Using Auto-Labeled Data

This script loads auto-labeled training and validation CSV files (e.g., train_auto.csv and val_auto.csv)
from the data/processed directory. It uses the "full_text" column (which includes title, flair, and selftext)
to generate TF-IDF features, trains a Logistic Regression classifier with balanced class weights,
and evaluates performance on the validation set by printing a classification report.

Usage:
    python baseline_train.py --train data/processed/train_auto.csv --val data/processed/val_auto.csv --max_features 10000
"""

import pandas as pd
import argparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

def load_and_prepare_data(train_path, val_path):
    # Load training and validation data
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    # Ensure "full_text" column exists; if not, create it by combining title and selftext.
    if "full_text" not in train_df.columns:
        train_df["full_text"] = (train_df["title"].fillna("") + " " + train_df["selftext"].fillna("")).str.strip()
    else:
        train_df["full_text"] = train_df["full_text"].fillna("")
    
    if "full_text" not in val_df.columns:
        val_df["full_text"] = (val_df["title"].fillna("") + " " + val_df["selftext"].fillna("")).str.strip()
    else:
        val_df["full_text"] = val_df["full_text"].fillna("")
    
    return train_df, val_df

def vectorize_text(train_texts, val_texts, max_features):
    # Initialize TF-IDF vectorizer with unigrams and bigrams, removing English stop words.
    vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), stop_words="english")
    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)
    return X_train, X_val, vectorizer

def train_and_evaluate(train_path, val_path, max_features):
    train_df, val_df = load_and_prepare_data(train_path, val_path)
    print(f"Training samples: {len(train_df)}, Validation samples: {len(val_df)}")
    
    # Use the "full_text" column for feature extraction.
    X_train, X_val, vectorizer = vectorize_text(train_df["full_text"], val_df["full_text"], max_features)
    
    # Use the auto-labeled column as target
    y_train = train_df["auto_label"]
    y_val = val_df["auto_label"]
    
    # Train Logistic Regression with balanced class weights.
    model = LogisticRegression(class_weight="balanced", max_iter=1000, solver="liblinear")
    model.fit(X_train, y_train)
    
    # Evaluate on validation set.
    y_pred = model.predict(X_val)
    print("\nBaseline Model Performance:")
    print(classification_report(y_val, y_pred))
    
    return model, vectorizer

def main():
    parser = argparse.ArgumentParser(description="Baseline training for distress detection using auto-labeled data.")
    parser.add_argument("--train", type=str, default="data/processed/train_auto.csv", help="Path to auto-labeled training CSV file.")
    parser.add_argument("--val", type=str, default="data/processed/val_auto.csv", help="Path to auto-labeled validation CSV file.")
    parser.add_argument("--max_features", type=int, default=10000, help="Maximum number of features for the TF-IDF vectorizer.")
    args = parser.parse_args()
    
    train_and_evaluate(args.train, args.val, args.max_features)

if __name__ == "__main__":
    main()
