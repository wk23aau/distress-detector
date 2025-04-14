#!/usr/bin/env python3
"""
preprocessing.py

A Multimodal AI Approach to Emotional Distress Detection on Reddit Posts

This script processes Reddit posts for mental health analysis using MentalBERT.
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

# Add these imports at the top
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load configuration values
HF_TOKEN = os.getenv("HF_TOKEN")  # Matches .env variable name
MODEL_NAME = os.getenv("MODEL_NAME")  # Now loaded from .env

# Validate required variables
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file")
if not MODEL_NAME:
    raise ValueError("MODEL_NAME not found in .env file")


# # Load environment variables
# load_dotenv()
# HF_TOKEN = os.getenv("")

# Model configuration
MODEL_NAME = "mental/mental-bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# File paths (Update these paths as needed)
INPUT_PATH = r"D:\distress-detector\data\combined\combined_posts.csv"
OUTPUT_PATH = r"D:\distress-detector\data\processed\processed_data.csv"

def load_dataset(file_path):
    """Load dataset from CSV or JSON"""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    if file_path.endswith('.json'):
        return pd.read_json(file_path)
    raise ValueError("Unsupported format. Use CSV or JSON.")

def clean_text(text):
    """Normalize and clean text content"""
    text = text.lower()
    text = re.sub(r'http\S+', '', text)        # Remove URLs
    text = re.sub(r'[^\w\s]', '', text)        # Remove punctuation
    return re.sub(r'\s+', ' ', text).strip()   # Normalize whitespace

def anonymize_author(author):
    """Anonymize author names with MD5 hash"""
    if pd.isna(author) or author == "[deleted]":
        return author
    return hashlib.md5(author.encode('utf-8')).hexdigest()

def extract_metadata_features(df):
    """Extract temporal and behavioral features"""
    df['created_utc'] = pd.to_datetime(df['created_utc'], errors='coerce')
    df['hour'] = df['created_utc'].dt.hour
    df['day_of_week'] = df['created_utc'].dt.dayofweek
    df['comment_score_ratio'] = df.apply(
        lambda row: row['num_comments'] / row['score'] if row['score'] != 0 else 0, 
        axis=1
    )
    return df

def annotate_text(text):
    """Annotate text using MentalBERT pipeline"""
    try:
        return annotator(text)[0]
    except Exception as e:
        logger.error(f"Annotation error: {e}")
        return {"error": str(e)}

def main():
    logger.info(f"Processing dataset from {INPUT_PATH}")
    
    # Load and validate data
    try:
        df = load_dataset(INPUT_PATH)
        required_columns = ['text', 'created_utc', 'author', 'num_comments', 'score']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)

    # Preprocess text
    df['combined_text'] = df['text'].fillna('')
    if 'title' in df.columns:
        df['combined_text'] = df['title'].fillna('') + " " + df['combined_text']
    df['clean_text'] = df['combined_text'].apply(clean_text)
    df['author'] = df['author'].apply(anonymize_author)
    df = extract_metadata_features(df)

    # Initialize annotation pipeline
    global annotator
    try:
        annotator = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer
        )
    except Exception as e:
        logger.error(f"Pipeline initialization failed: {e}")
        sys.exit(1)

    # Perform annotation
    df['annotation'] = df['clean_text'].apply(annotate_text)
    df['label'] = df['annotation'].apply(lambda x: x.get('label'))
    df['confidence'] = df['annotation'].apply(lambda x: x.get('score'))

    # Save results
    try:
        if OUTPUT_PATH.endswith('.csv'):
            df.to_csv(OUTPUT_PATH, index=False)
        elif OUTPUT_PATH.endswith('.json'):
            df.to_json(OUTPUT_PATH, orient='records')
        logger.info(f"Processing completed. Output saved to {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Output failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()