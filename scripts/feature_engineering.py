import pandas as pd
import numpy as np
from sklearn.feature_selection import VarianceThreshold, SelectFromModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from transformers import BertTokenizer, BertModel
import torch
from tqdm import tqdm
from textblob import TextBlob

# Configuration
INPUT_PATH = "data/processed/TrueOffMyChest_cleaned.csv"
OUTPUT_PATH = "data/processed/TrueOffMyChest_features.csv"

def generate_bert_embeddings(texts, max_length=512):
    """Generate BERT [CLS] token embeddings for text data"""
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()
    
    embeddings = []
    with torch.no_grad():
        for text in tqdm(texts, desc="Generating BERT embeddings"):
            inputs = tokenizer(text, return_tensors='pt', 
                            padding='max_length', truncation=True,
                            max_length=max_length)
            outputs = model(**inputs)
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            embeddings.append(cls_embedding)
    return np.array(embeddings)

def extract_sentiment_features(text):
    """Extract sentiment polarity and subjectivity using TextBlob"""
    analysis = TextBlob(text)
    return analysis.sentiment.polarity, analysis.sentiment.subjectivity

def engineer_features(df):
    # Combine title and selftext with fallback to empty strings
    df["title"] = df["title"].fillna("")  # Ensure no NaNs in title
    df["selftext"] = df["selftext"].fillna("")  # Ensure no NaNs in selftext
    df["full_text"] = df["title"] + " " + df["selftext"]
    df["full_text"] = df["full_text"].replace("nan", "")  # Handle edge cases
    
    # Calculate text length (now safe from NaNs)
    df["text_length"] = df["full_text"].apply(lambda x: len(x) if isinstance(x, str) else 0)
    
    # Sentiment features
    print("Extracting sentiment features...")
    df[["sentiment_polarity", "sentiment_subjectivity"]] = df["full_text"].apply(
        lambda x: pd.Series(extract_sentiment_features(x))
    )
    
    # Engagement features
    print("Engineering engagement features...")
    df["log_score"] = np.log1p(df["score"])
    df["log_comments"] = np.log1p(df["num_comments"])
    df["engagement_ratio"] = df["score"] / (df["num_comments"] + 1)
    
    # Temporal features
    print("Extracting temporal features...")
    df["datetime"] = pd.to_datetime(df["created_utc"], utc=True)  # Fixed datetime conversion
    df["post_hour"] = df["datetime"].dt.hour
    df["post_dayofweek"] = df["datetime"].dt.dayofweek
    
    # BERT embeddings (dimensionality reduction)
    print("Generating BERT embeddings...")
    bert_embeddings = generate_bert_embeddings(df["full_text"].tolist())
    bert_df = pd.DataFrame(bert_embeddings, columns=[f"bert_{i}" for i in range(768)])
    
    # Select only verified columns
    base_features = [
        "text_length", "sentiment_polarity", "sentiment_subjectivity",
        "log_score", "log_comments", "engagement_ratio",
        "post_hour", "post_dayofweek"
    ]
    
    # Add has_media only if it exists
    if "has_media" in df.columns:
        base_features.append("has_media")
    else:
        print("⚠️ 'has_media' column not found - excluding from features")
    
    # Combine all features
    feature_df = pd.concat([
        df[base_features],
        bert_df
    ], axis=1)
    
    return feature_df

def select_features(X, y):
    """Apply feature selection techniques"""
    # Variance threshold
    print("Applying variance threshold...")
    selector = VarianceThreshold(threshold=0.01)
    X_high_var = selector.fit_transform(X)
    
    # Correlation analysis
    print("Removing correlated features...")
    corr_matrix = pd.DataFrame(X_high_var).corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
    X_uncorr = np.delete(X_high_var, to_drop, axis=1)
    
    # Model-based selection
    print("Selecting features with Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    sfm = SelectFromModel(rf, threshold="median")
    X_selected = sfm.fit_transform(X_uncorr, y)
    
    return X_selected, sfm.get_support(indices=True)

if __name__ == "__main__":
    # Load data
    df = pd.read_csv(INPUT_PATH)
    
    # Engineer features
    print("Starting feature engineering...")
    X = engineer_features(df)
    y = df["label"]  # Now guaranteed to exist
    
    # Feature selection
    print("\nStarting feature selection...")
    X_selected, selected_indices = select_features(X, y)
    
    # Create final feature DataFrame
    selected_features = X.columns[selected_indices]
    final_df = pd.DataFrame(X_selected, columns=selected_features)
    final_df["label"] = y.values
    
    # Save processed features
    print(f"\nSaving {len(final_df)} samples with {len(selected_features)} features")
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Features saved to {OUTPUT_PATH}")