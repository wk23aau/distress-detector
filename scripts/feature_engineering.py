import os
import pandas as pd
from tqdm import tqdm
from transformers import BertTokenizer, BertModel
import torch
import numpy as np

# Configuration
INPUT_DIR = "data/processed"
OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load pre-trained BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")

def generate_bert_embeddings(texts):
    """Generate BERT embeddings for a list of texts"""
    embeddings = []
    with torch.no_grad():
        for text in tqdm(texts, desc="Generating BERT embeddings"):
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            outputs = model(**inputs)
            # Use the [CLS] token's embedding as the sentence representation
            embeddings.append(outputs.last_hidden_state[:, 0, :].numpy())
    return np.vstack(embeddings)

def engineer_features(df):
    """Engineer additional features from the dataset"""
    df["full_text"] = df["title"].fillna("") + " " + df["selftext"].fillna("")
    df["text_length"] = df["full_text"].apply(len)
    df["engagement_score"] = df["score"] + df["num_comments"]
    return df

def main():
    """Main function to generate features for train, val, and test sets"""
    datasets = ["train", "val", "test"]
    for dataset in datasets:
        print(f"Processing {dataset}.csv...")
        
        # Load dataset
        input_path = os.path.join(INPUT_DIR, f"{dataset}.csv")
        df = pd.read_csv(input_path)
        
        # Engineer features
        df = engineer_features(df)
        
        # Generate BERT embeddings
        bert_embeddings = generate_bert_embeddings(df["full_text"])
        bert_df = pd.DataFrame(bert_embeddings, columns=[f"bert_{i}" for i in range(768)])
        
        # Combine features
        final_df = pd.concat([df, bert_df], axis=1)
        
        # Save processed features
        output_path = os.path.join(OUTPUT_DIR, f"{dataset}_features.csv")
        final_df.to_csv(output_path, index=False)
        print(f"✅ Saved {dataset}_features.csv with shape {final_df.shape}")

if __name__ == "__main__":
    main()