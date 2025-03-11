#!/usr/bin/env python3
"""
Preprocessing Data Script for Distress Detection Model

This script processes raw Reddit post data from multiple JSON/TXT files,
applies cleaning and labeling, and saves a consolidated CSV file.

Usage:
    python preprocessing_data.py --input_dir data/raw/reddit-posts --output_dir data/processed
"""

import os
import json
import re
import argparse
import logging
from tqdm import tqdm
import pandas as pd
import emoji

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def clean_text(text):
    """
    Clean text by:
      - Converting emojis to text (without delimiters)
      - Converting to lowercase
      - Removing URLs, email addresses, and phone numbers
      - Removing unwanted special characters (while preserving key punctuation: !, ?, .)
      - Normalizing whitespace
    """
    if not text or pd.isna(text) or text in ["[deleted]", "[removed]"]:
        return ""
    
    text = emoji.demojize(text, delimiters=("", ""))
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"\+?\d[\d -]{8,12}\d", "", text)
    text = re.sub(r"[^\w\s!?\.]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def process_post(post):
    """
    Process a single Reddit post:
      - Clean key text fields.
      - Combine title and selftext (handled later via full_text creation).
      - Label post as distress (1) if its cleaned link_flair starts with "content warning" (case-insensitive).
    """
    processed = {
        "id": post.get("id", ""),
        "title": clean_text(post.get("title", "")),
        "selftext": clean_text(post.get("selftext", "")),
        "subreddit": post.get("subreddit", ""),
        "created_utc": post.get("created_utc", 0),
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.0),
        "author_flair": clean_text(post.get("author_flair_text", "")),
        "link_flair": clean_text(post.get("link_flair", "")),
        "has_media": 1 if post.get("media") or post.get("preview") else 0
    }
    
    # Label post as distress if link_flair starts with "content warning"
    if processed["link_flair"] and processed["link_flair"].strip().lower().startswith("content warning"):
        processed["label"] = 1
    else:
        processed["label"] = 0
    
    return processed

def load_and_combine_raw_data(input_dir):
    """
    Load all JSON/TXT files from the input directory and combine them into a single DataFrame.
    """
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith((".json", ".txt"))]
    if not files:
        raise FileNotFoundError(f"No JSON/TXT files found in {input_dir}")
    
    dataframes = []
    for filepath in files:
        logging.info(f"Loading file: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Handle common Reddit API structures
                if "data" in data:
                    if isinstance(data["data"], dict) and "children" in data["data"]:
                        data = [child["data"] for child in data["data"]["children"]]
                    else:
                        data = data["data"]
                else:
                    data = [data]
            elif not isinstance(data, list):
                data = []
            df = pd.DataFrame(data)
            dataframes.append(df)
            logging.info(f"Loaded {len(df)} records from {os.path.basename(filepath)}")
        except Exception as e:
            logging.error(f"Error loading {filepath}: {e}")
    
    if not dataframes:
        raise ValueError("No data loaded from input directory.")
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    logging.info(f"Combined data has {len(combined_df)} records.")
    return combined_df

def preprocess_data(df):
    """
    Preprocess the DataFrame:
      - Fill missing values in 'title' and 'selftext'.
      - Process each post using process_post().
    """
    for col in ["title", "selftext"]:
        df[col] = df[col].fillna("")
    
    processed_posts = []
    for _, post in tqdm(df.iterrows(), total=len(df), desc="Processing posts"):
        processed_posts.append(process_post(post))
    processed_df = pd.DataFrame(processed_posts)
    return processed_df

def main(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    combined_df = load_and_combine_raw_data(input_dir)
    processed_df = preprocess_data(combined_df)
    
    # Remove duplicates based on post ID
    before = len(processed_df)
    processed_df = processed_df.drop_duplicates(subset=["id"])
    after = len(processed_df)
    logging.info(f"Removed {before - after} duplicate posts.")
    
    output_path = os.path.join(output_dir, "TrueOffMyChest_cleaned.csv")
    processed_df.to_csv(output_path, index=False, encoding="utf-8")
    logging.info(f"Processed data saved to {output_path}")
    logging.info("Label distribution:")
    logging.info(processed_df["label"].value_counts())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess raw Reddit posts for distress detection.")
    parser.add_argument("--input_dir", type=str, default="data/raw/reddit-posts", help="Directory containing raw JSON/TXT files.")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Directory to save the processed CSV file.")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir)
