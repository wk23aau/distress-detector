#!/usr/bin/env python3
"""
Automated Labeling Pipeline for Distress Detection
Combines VADER, a transformer-based sentiment model, and an ABSA model
to automatically label posts as distress (1) or non-distress (0) without manual labor.

Usage:
    python auto_label.py --input_file data/processed/TrueOffMyChest_cleaned.csv --output_file data/processed/TrueOffMyChest_auto_labeled.csv
"""

import argparse
import pandas as pd
import numpy as np
import re
import emoji
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline

# Download VADER lexicon if not already downloaded
nltk.download('vader_lexicon')

# Initialize VADER sentiment analyzer
vader_analyzer = SentimentIntensityAnalyzer()

# Initialize a transformer-based sentiment analysis pipeline
# We explicitly set truncation parameters in our calls below
transformer_sentiment = pipeline(
    "sentiment-analysis", 
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

# For demonstration, we'll use the same model as a proxy for ABSA sentiment
absa_sentiment = pipeline(
    "sentiment-analysis", 
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

def clean_text(text):
    """
    Clean text by:
      - Converting emojis to text (without delimiters)
      - Lowercasing text
      - Removing URLs, emails, and phone numbers
      - Normalizing whitespace
    """
    if not text:
        return ""
    text = emoji.demojize(text, delimiters=("", ""))
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"\+?\d[\d -]{8,12}\d", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_vader_score(text):
    """Return the compound sentiment score from VADER."""
    scores = vader_analyzer.polarity_scores(text)
    return scores["compound"]

def get_transformer_sentiment(text):
    """Return the sentiment score from the transformer-based sentiment model.
       We pass truncation parameters to ensure inputs do not exceed the maximum length.
       Maps 'NEGATIVE' to a negative score, 'POSITIVE' to a positive score."""
    result = transformer_sentiment(text, truncation=True, max_length=512)[0]
    score = result["score"]
    label = result["label"]
    return -score if label.upper() == "NEGATIVE" else score

def get_absa_sentiment(text):
    """Return a proxy ABSA sentiment score using the transformer sentiment pipeline.
       We pass truncation parameters similarly."""
    result = absa_sentiment(text, truncation=True, max_length=512)[0]
    score = result["score"]
    label = result["label"]
    return -score if label.upper() == "NEGATIVE" else score

def auto_label_post(full_text, vader_threshold=-0.5, transformer_threshold=-0.5, absa_threshold=-0.5):
    """
    Automatically label a post as distress if:
      - VADER compound score is below vader_threshold, AND
      - Transformer sentiment score indicates negative sentiment (below transformer_threshold), AND
      - ABSA sentiment score indicates negative sentiment (below absa_threshold).
    Returns 1 if distress, 0 otherwise.
    """
    text = clean_text(full_text)
    
    vader_score = get_vader_score(text)
    transformer_score = get_transformer_sentiment(text)
    absa_score = get_absa_sentiment(text)
    
    # For a strict rule, require all three signals to be below thresholds
    if vader_score < vader_threshold and transformer_score < transformer_threshold and absa_score < absa_threshold:
        return 1
    else:
        return 0

def main(input_file, output_file):
    df = pd.read_csv(input_file)
    
    # Ensure full_text exists; if not, combine title and selftext.
    if "full_text" not in df.columns:
        df["full_text"] = (df["title"].fillna("") + " " + df["selftext"].fillna("")).str.strip()
    
    # Apply auto labeling to every post
    df["auto_label"] = df["full_text"].apply(auto_label_post)
    
    print("Auto-label distribution:")
    print(df["auto_label"].value_counts())
    
    df.to_csv(output_file, index=False)
    print(f"Saved auto-labeled data to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically label posts as distress or non-distress using VADER, Transformer, and ABSA.")
    parser.add_argument("--input_file", type=str, default="data/processed/TrueOffMyChest_cleaned.csv", help="Path to the processed CSV file.")
    parser.add_argument("--output_file", type=str, default="data/processed/TrueOffMyChest_auto_labeled.csv", help="Path to save the auto-labeled CSV file.")
    args = parser.parse_args()
    
    main(args.input_file, args.output_file)
