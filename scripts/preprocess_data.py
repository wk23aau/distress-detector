#!/usr/bin/env python3
"""
Preprocess Data Script for Supervised Distress Detection with Flair Inclusion

This script processes raw Reddit post data from multiple JSON/TXT files located in the
"data/raw/reddit-posts" directory. It cleans the "title", "selftext", and flair fields,
concatenates them into a "full_text" column (flair is appended between title and selftext),
retains labels (or defaults to 0 if not provided), removes duplicate posts based on the "id" field,
and saves the final deduplicated dataset as a CSV file for supervised training.

Usage:
    python preprocess_data.py --input_dir data/raw/reddit-posts --output_dir data/processed
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
      - Converting text to lowercase
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
      - Clean the "title" and "selftext" fields.
      - Retrieve flair from either "link_flair" or "link_flair_text" (if available) and clean it.
      - Create a "full_text" field by concatenating the title, flair (if available), and selftext.
      - Retain the original label if provided; otherwise, default to 0.
    """
    cleaned_title = clean_text(post.get("title", ""))
    cleaned_selftext = clean_text(post.get("selftext", ""))
    
    # Retrieve flair: try "link_flair" first; if not present, try "link_flair_text"
    raw_flair = post.get("link_flair") or post.get("link_flair_text", "")
    cleaned_flair = clean_text(raw_flair)
    
    # Create full_text by combining title, flair (if available), and selftext
    if cleaned_flair:
        full_text = f"{cleaned_title} {cleaned_flair} {cleaned_selftext}".strip()
    else:
        full_text = f"{cleaned_title} {cleaned_selftext}".strip()
    
    processed = {
        "id": post.get("id", ""),
        "title": cleaned_title,
        "selftext": cleaned_selftext,
        "flair": cleaned_flair,  # We keep the cleaned flair for reference
        "subreddit": post.get("subreddit", ""),
        "created_utc": post.get("created_utc", 0),
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.0),
        "has_media": 1 if post.get("media") or post.get("preview") else 0,
        "full_text": full_text
    }
    
    # Retain the label if present; otherwise, default to 0.
    processed["label"] = post.get("label", 0)
    
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
            # Handle common Reddit API structures
            if isinstance(data, dict):
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
      - Fill missing values for "title" and "selftext".
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
    
    # Load and combine raw data from all files
    combined_df = load_and_combine_raw_data(input_dir)
    
    # Preprocess the combined DataFrame
    processed_df = preprocess_data(combined_df)
    
    # Remove duplicate posts based on the "id" field
    before = len(processed_df)
    processed_df = processed_df.drop_duplicates(subset=["id"])
    after = len(processed_df)
    logging.info(f"Removed {before - after} duplicate posts.")
    
    output_path = os.path.join(output_dir, "TrueOffMyChest_cleaned.csv")
    processed_df.to_csv(output_path, index=False, encoding="utf-8")
    logging.info(f"Processed data saved to {output_path}")
    
    if "label" in processed_df.columns:
        logging.info("Label distribution:")
        logging.info(processed_df["label"].value_counts())
    else:
        logging.info("No label column found in processed data.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess raw Reddit posts for supervised distress detection (including flair in full_text).")
    parser.add_argument("--input_dir", type=str, default="data/raw/reddit-posts", help="Directory containing raw JSON/TXT files.")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Directory to save the processed CSV file.")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir)
