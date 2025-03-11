# """
# Baseline Model Training Script for Distress Detection

# This script:
# 1. Loads training and validation datasets from CSV files.
# 2. Fills missing values and combines "title" and "selftext" into "full_text".
# 3. Extracts TF-IDF features using unigrams and bigrams.
# 4. Trains a Logistic Regression model with balanced class weights.
# 5. Evaluates the model and prints a classification report.

# Usage:
#     python baseline_train.py --train data/processed/train.csv --val data/processed/val.csv --max_features 10000
# """

# import pandas as pd
# import argparse
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import classification_report

# def load_data(train_path, val_path):
#     """Load and fill missing values in the training and validation CSV files."""
#     train_df = pd.read_csv(train_path)
#     val_df = pd.read_csv(val_path)
    
#     # Fill missing values in text fields
#     for col in ["title", "selftext"]:
#         train_df[col] = train_df[col].fillna("")
#         val_df[col] = val_df[col].fillna("")
    
#     return train_df, val_df

# def combine_text(df):
#     """Combine title and selftext into a single 'full_text' field."""
#     df["full_text"] = (df["title"] + " " + df["selftext"]).str.strip()
#     return df

# def vectorize_text(train_texts, val_texts, max_features):
#     """
#     Vectorize text using TF-IDF with unigrams and bigrams.
    
#     Returns the transformed training and validation matrices along with the vectorizer.
#     """
#     vectorizer = TfidfVectorizer(
#         max_features=max_features,
#         ngram_range=(1, 2),
#         stop_words="english"
#     )
#     X_train = vectorizer.fit_transform(train_texts)
#     X_val = vectorizer.transform(val_texts)
#     return X_train, X_val, vectorizer

# def train_model(X_train, y_train):
#     """Train a Logistic Regression model using balanced class weights."""
#     model = LogisticRegression(class_weight="balanced", max_iter=1000, solver="liblinear")
#     model.fit(X_train, y_train)
#     return model

# def evaluate_model(model, X_val, y_val):
#     """Evaluate the model and return the classification report."""
#     y_pred = model.predict(X_val)
#     report = classification_report(y_val, y_pred)
#     return report

# def main(args):
#     # Load and preprocess data
#     train_df, val_df = load_data(args.train, args.val)
#     train_df = combine_text(train_df)
#     val_df = combine_text(val_df)
    
#     print(f"Training samples: {len(train_df)} | Validation samples: {len(val_df)}")
    
#     # Vectorize text
#     X_train, X_val, _ = vectorize_text(train_df["full_text"], val_df["full_text"], args.max_features)
#     y_train = train_df["label"]
#     y_val = val_df["label"]
    
#     # Train model
#     model = train_model(X_train, y_train)
    
#     # Evaluate model
#     report = evaluate_model(model, X_val, y_val)
#     print("\nBaseline Model Performance:")
#     print(report)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Baseline model training using TF-IDF and Logistic Regression for distress detection.")
#     parser.add_argument("--train", type=str, default="data/processed/train.csv", help="Path to the training CSV file.")
#     parser.add_argument("--val", type=str, default="data/processed/val.csv", help="Path to the validation CSV file.")
#     parser.add_argument("--max_features", type=int, default=10000, help="Maximum number of features for TF-IDF vectorizer.")
#     args = parser.parse_args()
    
#     main(args)

import pandas as pd
df = pd.read_csv("data/processed/train.csv")
print(df.columns)
print(df["link_flair"].value_counts())


