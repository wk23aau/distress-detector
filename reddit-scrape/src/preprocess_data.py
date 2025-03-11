import json
import os
import pandas as pd
import emoji
from cleantext import clean
from tqdm import tqdm

# Configuration
INPUT_DIR = "data/raw/reddit-posts"
OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text):
    """Remove emojis, URLs, and special characters from text"""
    if pd.isna(text) or text in ["[deleted]", "[removed]"]:
        return ""
    text = emoji.demojize(text, delimiters=("", ""))  # Remove emojis
    return clean(
        text,
        no_urls=True,
        no_emails=True,
        no_phone_numbers=True,
        lower=False,
        fix_unicode=True
    )

def process_post(post):
    """Extract and clean relevant fields from a Reddit post"""
    processed = {
        "id": post.get("id", ""),
        "title": clean_text(post.get("title", "")),
        "selftext": clean_text(post.get("selftext", "")),
        "subreddit": post.get("subreddit", ""),
        "created_utc": post.get("created_utc", 0),  # Keep as timestamp
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.0),
        "author_flair": clean_text(post.get("author_flair_text", "")),
        "link_flair": clean_text(post.get("link_flair_text", "")),
        "has_media": 1 if post.get("media") or post.get("preview") else 0
    }
    
    # Add distress label based on link_flair (Objective 1.4.1)
    distress_flairs = ["Support Needed", "Crisis", "Trigger Warning", "Mental Health"]
    processed["label"] = 1 if processed["link_flair"] in distress_flairs else 0
    
    return processed

def main():
    """Process all JSON files and save both individual and combined CSVs"""
    all_processed_posts = []  # Accumulate all posts across files

    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith((".json", ".txt")):
            continue
        
        input_path = os.path.join(INPUT_DIR, filename)
        print(f"Processing {filename}...")
        
        try:
            with open(input_path, "r") as f:
                raw_posts = json.load(f)
        except json.JSONDecodeError:
            print(f"  ⚠️ Skipping invalid JSON: {filename}")
            continue
        
        processed_posts = []
        for post in tqdm(raw_posts, desc=f"  Processing posts"):
            processed = process_post(post)
            
            # Skip posts with no content (empty title AND selftext)
            if processed["title"] or processed["selftext"]:
                processed_posts.append(processed)
        
        if not processed_posts:
            print(f"  ⚠️ No valid posts found in {filename}")
            continue
        
        # Save individual file
        df_individual = pd.DataFrame(processed_posts)
        output_filename = filename.replace(".json", ".csv").replace(".txt", ".csv")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        df_individual.to_csv(output_path, index=False)
        print(f"  ✅ Saved {len(processed_posts)} posts to {output_path}")
        
        # Add to combined dataset
        all_processed_posts.extend(processed_posts)
    
    # Save consolidated file
    if all_processed_posts:
        df_combined = pd.DataFrame(all_processed_posts)
        combined_path = os.path.join(OUTPUT_DIR, "TrueOffMyChest_cleaned.csv")
        df_combined.to_csv(combined_path, index=False)
        print(f"\n✅✅ Combined {len(all_processed_posts)} total posts to {combined_path}")

if __name__ == "__main__":
    main()