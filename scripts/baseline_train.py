# Script: baseline_train.py
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Load train and validation splits
train_df = pd.read_csv("data/processed/train.csv")
val_df = pd.read_csv("data/processed/val.csv")

# Combine text fields
train_df["full_text"] = train_df["title"] + " " + train_df["selftext"]
val_df["full_text"] = val_df["title"] + " " + val_df["selftext"]

# TF-IDF Vectorization
tfidf = TfidfVectorizer(max_features=10000)
X_train = tfidf.fit_transform(train_df["full_text"])
X_val = tfidf.transform(val_df["full_text"])
y_train = train_df["label"]
y_val = val_df["label"]

# Train baseline model
model = LogisticRegression(class_weight="balanced", max_iter=1000)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_val)
print("Baseline Model Performance:")
print(classification_report(y_val, y_pred))