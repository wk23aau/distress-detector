#!/usr/bin/env python3
"""
Automated Labeling Pipeline for Distress Detection

This script loads a processed CSV file (e.g., TrueOffMyChest_cleaned.csv) that contains posts,
applies three unsupervised sentiment analyses (VADER, a transformer sentiment model, and a proxy ABSA model),
and then automatically assigns a distress label (1 for distress, 0 for non‑distress) based on preset thresholds.
No manual annotation is required.

Usage:
    python auto_label.py --input_file data/processed/TrueOffMyChest_cleaned.csv --output_file data/processed/TrueOffMyChest_auto_labeled.csv
"""

import argparse
import pandas as pd
import re
import emoji
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline

# Download VADER lexicon if not already downloaded
nltk.download('vader_lexicon')

# Initialize VADER sentiment analyzer
vader_analyzer = SentimentIntensityAnalyzer()

# Initialize a transformer-based sentiment analysis pipeline.
# (We use DistilBERT fine-tuned on SST-2; adjust model as needed.)
transformer_sentiment = pipeline(
    "sentiment-analysis", 
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

# For a proxy ABSA sentiment signal, we use the same transformer sentiment pipeline.
absa_sentiment = pipeline(
    "sentiment-analysis", 
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

def clean_text(text):
    """
    Clean text by:
      - Converting emojis to text (without colon delimiters)
      - Converting text to lowercase
      - Removing URLs, email addresses, and phone numbers
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
    """
    Return a sentiment score from the transformer-based sentiment model.
    We use truncation with max_length=512 to avoid errors.
    Maps 'NEGATIVE' to a negative score and 'POSITIVE' to a positive score.
    """
    result = transformer_sentiment(text, truncation=True, max_length=512)[0]
    score = result["score"]
    label = result["label"]
    return -score if label.upper() == "NEGATIVE" else score

def get_absa_sentiment(text):
    """
    Return a proxy ABSA sentiment score.
    For demonstration purposes, we use the same transformer sentiment pipeline.
    Again, use truncation parameters.
    """
    result = absa_sentiment(text, truncation=True, max_length=512)[0]
    score = result["score"]
    label = result["label"]
    return -score if label.upper() == "NEGATIVE" else score

def auto_label_post(full_text, vader_threshold=-0.5, transformer_threshold=-0.5, absa_threshold=-0.5):
    """
    Automatically label a post as distress (1) if:
      - VADER compound score is below vader_threshold, AND
      - Transformer sentiment score is below transformer_threshold, AND
      - ABSA sentiment score is below absa_threshold.
    Otherwise, label as non‑distress (0).

    You can adjust the thresholds as needed.
    """
    text = clean_text(full_text)
    vader_score = get_vader_score(text)
    transformer_score = get_transformer_sentiment(text)
    absa_score = get_absa_sentiment(text)
    
    # For a strict rule, require all three sentiment signals to indicate negativity.
    if vader_score < vader_threshold and transformer_score < transformer_threshold and absa_score < absa_threshold:
        return 1
    else:
        return 0

def main(input_file, output_file):
    df = pd.read_csv(input_file)
    
    # Ensure a full_text column exists; if not, create it from title and selftext.
    if "full_text" not in df.columns:
        df["full_text"] = (df["title"].fillna("") + " " + df["selftext"].fillna("")).str.strip()
    
    # Apply the auto-labeling function to every post.
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
