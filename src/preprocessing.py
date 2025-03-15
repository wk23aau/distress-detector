#!/usr/bin/env python3
"""
preprocessing.py

A Multimodal AI Approach to Emotional Distress Detection on Reddit Posts

This script prompts the user to select the input file (CSV/JSON) and the output folder.
It then loads the raw dataset, processes text and metadata, anonymizes sensitive fields,
and applies annotation using a MentalBERT-based pipeline. The processed data is saved
as "processed_data.csv" in the selected output folder.
"""

import re
import os
import sys
import logging
import hashlib
from datetime import datetime
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from dotenv import load_dotenv
from tqdm import tqdm

# For file dialogs
import tkinter as tk
from tkinter import filedialog

# Hide the root tkinter window
root = tk.Tk()
root.withdraw()

def prompt_for_input_file():
    """Prompt the user to select an input CSV or JSON file."""
    input_file = filedialog.askopenfilename(
        title="Select Input File (CSV or JSON)",
        filetypes=[("CSV Files", "*.csv"), ("JSON Files", "*.json")]
    )
    if not input_file:
        raise ValueError("No input file selected.")
    return input_file

def prompt_for_output_folder():
    """Prompt the user to select an output folder."""
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    if not output_folder:
        raise ValueError("No output folder selected.")
    return output_folder

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file. Please add your Hugging Face token.")

MODEL_NAME = "mental/mental-bert-base-uncased"

# Manually load model and tokenizer with the token
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)

# Initialize the pipeline with truncation parameters to handle long sequences
annotator = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    truncation=True,
    max_length=512
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Prompt user for input file and output folder
try:
    INPUT_PATH = prompt_for_input_file()
    output_folder = prompt_for_output_folder()
    OUTPUT_PATH = os.path.join(output_folder, "processed_data.csv")
    logger.info(f"Input file selected: {INPUT_PATH}")
    logger.info(f"Output folder selected: {output_folder}")
except Exception as e:
    logger.error(f"Error selecting files: {e}")
    sys.exit(1)

def load_dataset(file_path):
    """Load dataset from a CSV or JSON file."""
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.json'):
        df = pd.read_json(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or JSON file.")
    return df

def clean_text(text):
    """Clean and normalize text:
       - Lowercase the text.
       - Remove URLs.
       - Remove punctuation.
       - Remove extra whitespace.
    """
    text = text.lower()
    text = re.sub(r'http\S+', '', text)           # Remove URLs
    text = re.sub(r'[^\w\s]', '', text)             # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()        # Remove extra spaces/newlines
    return text

def anonymize_author(author):
    """Anonymize author names using MD5 hash for privacy."""
    if pd.isna(author) or author == "[deleted]":
        return author
    return hashlib.md5(author.encode('utf-8')).hexdigest()

def extract_metadata_features(df):
    """Extract additional temporal and behavioral features from metadata.
    
    Features added:
      - Hour of day and day of week from created_utc.
      - Comment-to-score ratio as a behavioral cue.
    """
    if not pd.api.types.is_datetime64_any_dtype(df['created_utc']):
        df['created_utc'] = pd.to_datetime(df['created_utc'], errors='coerce')
    df['hour'] = df['created_utc'].dt.hour
    df['day_of_week'] = df['created_utc'].dt.dayofweek  # Monday=0, Sunday=6
    df['comment_score_ratio'] = df.apply(
        lambda row: row['num_comments'] / row['score'] if row['score'] != 0 else 0, axis=1
    )
    return df

def annotate_text(text, annotator):
    """Annotate text using the provided MentalBERT pipeline.
       Returns the annotation result (typically a dict with keys such as 'label' and 'score').
    """
    try:
        result = annotator(text)[0]
        return result
    except Exception as e:
        logger.error(f"Annotation error for text starting with '{text[:30]}...': {e}")
        return {"error": str(e)}

def main():
    logger.info(f"Processing dataset from {INPUT_PATH}")
    try:
        df = load_dataset(INPUT_PATH)
        logger.info(f"Loaded dataset with {len(df)} rows.")
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        sys.exit(1)

    # Verify required columns exist
    required_columns = ['text', 'created_utc', 'author', 'num_comments', 'score']
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}. Available columns: {list(df.columns)}")
            sys.exit(1)

    # Combine title and text (if title exists) for richer context
    if 'title' in df.columns:
        df['combined_text'] = df['title'].fillna('') + " " + df['text'].fillna('')
    else:
        df['combined_text'] = df['text'].fillna('')
    df['clean_text'] = df['combined_text'].apply(clean_text)
    logger.info("Completed text cleaning.")

    # Anonymize sensitive author information
    df['author'] = df['author'].apply(anonymize_author)
    logger.info("Anonymized author names.")

    # Extract metadata features
    df = extract_metadata_features(df)
    logger.info("Extracted metadata features.")

    # Annotate text using MentalBERT with detailed logging
    annotations = []
    total = len(df)
    logger.info("Starting annotation of posts...")
    for idx, row in tqdm(df.iterrows(), total=total, desc="Annotating posts", leave=True):
        text = row['clean_text']
        result = annotate_text(text, annotator)
        annotations.append(result)
        if (idx + 1) % 1000 == 0:
            logger.info(f"Annotated {idx + 1} posts out of {total}")
    df['annotation'] = annotations
    df['label'] = df['annotation'].apply(lambda x: x.get('label') if isinstance(x, dict) else None)
    df['score'] = df['annotation'].apply(lambda x: x.get('score') if isinstance(x, dict) else None)
    logger.info("Completed annotation of text.")

    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Save the processed dataset
    try:
        if OUTPUT_PATH.endswith('.csv'):
            df.to_csv(OUTPUT_PATH, index=False)
        elif OUTPUT_PATH.endswith('.json'):
            df.to_json(OUTPUT_PATH, orient='records')
        else:
            raise ValueError("Unsupported output file format. Use CSV or JSON.")
        logger.info(f"Processed data saved to {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Error saving processed data: {e}")

if __name__ == "__main__":
    main()
