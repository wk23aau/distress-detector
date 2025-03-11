#!/usr/bin/env python3
"""
Check Unique IDs in Combined JSON File

This script loads a combined JSON file (e.g., combined.json) from the "data/raw/reddit-posts" directory,
then computes and prints:
  - The total number of records.
  - The number of unique values in the "id" field.

Usage:
    python check_unique_ids.py --input_file data/raw/reddit-posts/combined.json
"""

import json
import argparse

def main(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total_records = len(data)
    unique_ids = {post.get("id") for post in data if post.get("id") is not None}
    
    print(f"Total records: {total_records}")
    print(f"Unique IDs count: {len(unique_ids)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check unique IDs in a combined JSON file.")
    parser.add_argument("--input_file", type=str, default="data/raw/reddit-posts/combined.json",
                        help="Path to the combined JSON file.")
    args = parser.parse_args()
    
    main(args.input_file)
