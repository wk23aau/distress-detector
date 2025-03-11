#!/usr/bin/env python3
"""
Preprocess Data Script for Distress Detection Model

This script processes raw Reddit post data from multiple JSON/TXT files and saves a consolidated CSV.
Improvements include:
- Command-line arguments for input/output directories.
- Lowercasing and selective preservation of punctuation.
- Robust JSON file handling.
- Removal of duplicate posts.
- Enhanced logging.
"""

import os
import json
import re
import argparse
import logging
from tqdm import tqdm
import pandas as pd
import emoji

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def clean_text(text):
    """
    Clean text by:
      - Removing emojis (converted to text)
      - Converting to lowercase
      - Removing URLs, email addresses, phone numbers
      - Removing unwanted special characters while preserving key punctuation (!, ?, .)
      - Normalizing whitespace
    """
    if pd.isna(text) or text in ["[deleted]", "[removed]"]:
        return ""
    
    # Convert emojis to text without colon delimiters
    text = emoji.demojize(text, delimiters=("", ""))
    
    # Normalize case
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)
    
    # Remove email addresses
    text = re.sub(r"\S+@\S+", "", text)
    
    # Remove phone numbers
    text = re.sub(r"\+?\d[\d -]{8,12}\d", "", text)
    
    # Remove unwanted characters but preserve punctuation that might indicate emotion
    text = re.sub(r"[^\w\s!?\.]", "", text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def process_post(post):
    """
    Extract and clean relevant fields from a Reddit post.
    Returns a dictionary of processed data.
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
        "link_flair": clean_text(post.get("link_flair_text", "")),
        "has_media": 1 if post.get("media") or post.get("preview") else 0
    }
    
    # Label distress: compare in a case-insensitive way by ensuring text is already lowercased
    distress_flairs = ["support needed", "crisis", "trigger warning", "mental health"]
    processed["label"] = 1 if processed["link_flair"] in distress_flairs else 0
    
    return processed

def load_json_file(filepath):
    """
    Load a JSON file, handling both list and dictionary formats.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # Handle possible Reddit API structure
                if "data" in data:
                    if isinstance(data["data"], dict) and "children" in data["data"]:
                        data = [child["data"] for child in data["data"]["children"]]
                    else:
                        data = data["data"]
            elif not isinstance(data, list):
                data = []
            return data
    except Exception as e:
        logging.error(f"Error loading {filepath}: {e}")
        return []

def process_files(input_dir, output_dir):
    """
    Process all JSON/TXT files in the input directory.
    Save individual CSVs for traceability and return a list of all processed posts.
    """
    all_posts = []
    for filename in os.listdir(input_dir):
        if not filename.endswith((".json", ".txt")):
            continue
        
        filepath = os.path.join(input_dir, filename)
        logging.info(f"Processing file: {filename}")
        raw_data = load_json_file(filepath)
        if not raw_data:
            logging.warning(f"No valid data in {filename}. Skipping.")
            continue
        
        processed_posts = []
        for post in tqdm(raw_data, desc=f"  Processing posts in {filename}", leave=False):
            processed = process_post(post)
            # Skip posts with no meaningful content
            if processed["title"] or processed["selftext"]:
                processed_posts.append(processed)
        
        if processed_posts:
            # Save individual file (optional for traceability)
            df_individual = pd.DataFrame(processed_posts)
            individual_filename = os.path.splitext(filename)[0] + ".csv"
            individual_path = os.path.join(output_dir, individual_filename)
            df_individual.to_csv(individual_path, index=False, encoding="utf-8")
            logging.info(f"Saved {len(processed_posts)} posts to {individual_filename}")
            all_posts.extend(processed_posts)
        else:
            logging.warning(f"No valid posts found in {filename}")
    
    return all_posts

def main(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    all_processed_posts = process_files(input_dir, output_dir)
    if not all_processed_posts:
        logging.error("No processed posts found. Exiting.")
        return
    
    # Remove duplicates based on post ID
    df_combined = pd.DataFrame(all_processed_posts)
    initial_count = len(df_combined)
    df_combined.drop_duplicates(subset=["id"], inplace=True)
    final_count = len(df_combined)
    logging.info(f"Removed {initial_count - final_count} duplicate posts.")
    
    combined_path = os.path.join(output_dir, "TrueOffMyChest_cleaned.csv")
    df_combined.to_csv(combined_path, index=False, encoding="utf-8")
    logging.info(f"Final consolidated dataset saved to {combined_path} with {final_count} posts")
    logging.info("Label distribution:")
    logging.info(df_combined["label"].value_counts())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess Reddit posts for distress detection.")
    parser.add_argument("--input_dir", type=str, default="data/raw/reddit-posts", help="Directory containing raw JSON/TXT files.")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Directory to save processed CSV files.")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir)
