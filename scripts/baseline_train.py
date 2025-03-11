#!/usr/bin/env python3
"""
Baseline Training Script for Distress Detection using TF-IDF and Logistic Regression

This script loads processed CSV files (train.csv and val.csv) from the data/processed directory.
It uses the "full_text" column if available; otherwise, it creates one by combining "title" and "selftext."
The text is then vectorized using TF-IDF, and a Logistic Regression model is trained and evaluated.
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
    
    # Check if "full_text" column exists; if not, create it
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
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words="english"
    )
    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)
    return X_train, X_val, vectorizer

def train_and_evaluate(train_path, val_path, max_features):
    train_df, val_df = load_and_prepare_data(train_path, val_path)
    print(f"Training samples: {len(train_df)}, Validation samples: {len(val_df)}")
    
    # Print label distribution for troubleshooting
    print("Train label distribution:")
    print(train_df['label'].value_counts())
    print("Validation label distribution:")
    print(val_df['label'].value_counts())
    
    if train_df['label'].nunique() < 2:
        raise ValueError(f"Training data has only one class: {train_df['label'].unique()[0]}")
    
    X_train, X_val, vectorizer = vectorize_text(train_df["full_text"], val_df["full_text"], max_features)
    y_train = train_df["label"]
    y_val = val_df["label"]
    
    model = LogisticRegression(class_weight="balanced", max_iter=1000, solver="liblinear")
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_val)
    print("\nBaseline Model Performance:")
    print(classification_report(y_val, y_pred))
    
    return model, vectorizer

def main():
    parser = argparse.ArgumentParser(description="Baseline training for distress detection using TF-IDF and Logistic Regression")
    parser.add_argument("--train", type=str, default="data/processed/train.csv", help="Path to processed training CSV")
    parser.add_argument("--val", type=str, default="data/processed/val.csv", help="Path to processed validation CSV")
    parser.add_argument("--max_features", type=int, default=10000, help="Maximum number of features for TF-IDF vectorizer")
    args = parser.parse_args()
    
    train_and_evaluate(args.train, args.val, args.max_features)

if __name__ == "__main__":
    main()
