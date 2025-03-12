#!/usr/bin/env python3
"""
Model Training Script for Distress Detection Using BERT Embeddings and Engineered Features

This script loads the combined feature matrix and labels saved as NumPy arrays 
(from the feature extraction step) in the directory (e.g., data/processed/features/),
performs a stratified train/validation split, and then trains a feed-forward neural network classifier
using PyTorch. The best-performing model based on validation F1 score is saved.

Usage:
    python model_train.py --features_path data/processed/features/features.npy --labels_path data/processed/features/labels.npy --model_dir models --epochs 10 --batch_size 32 --learning_rate 1e-4 --val_size 0.2 --random_state 42
"""

import os
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class FeaturesDataset(Dataset):
    def __init__(self, features, labels):
        self.features = features  # NumPy array
        self.labels = labels      # NumPy array
        
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y = torch.tensor(self.labels[idx], dtype=torch.float32)
        return x, y

class DistressClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dims=[256, 64]):
        super(DistressClassifier, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dims[1], 1)  # Output a single logit for binary classification
        )
    
    def forward(self, x):
        return self.model(x)

def evaluate(model, dataloader, device):
    model.eval()
    all_preds = []
    all_targets = []
    total_loss = 0.0
    criterion = nn.BCEWithLogitsLoss()
    
    with torch.no_grad():
        for features, labels in dataloader:
            features, labels = features.to(device), labels.to(device)
            outputs = model(features).squeeze(1)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * features.size(0)
            preds = torch.sigmoid(outputs) >= 0.5
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader.dataset)
    acc = accuracy_score(all_targets, all_preds)
    f1 = f1_score(all_targets, all_preds)
    return avg_loss, acc, f1

def train_model(args):
    # Load features and labels from NumPy files.
    if not os.path.exists(args.features_path):
        raise FileNotFoundError(f"Features file not found: {args.features_path}")
    if not os.path.exists(args.labels_path):
        raise FileNotFoundError(f"Labels file not found: {args.labels_path}")
        
    features = np.load(args.features_path)
    labels = np.load(args.labels_path).astype(np.float32)
    
    logging.info(f"Features shape: {features.shape}")
    logging.info(f"Labels shape: {labels.shape}")
    
    # Stratified split into train and validation sets
    indices = np.arange(len(labels))
    train_idx, val_idx = train_test_split(
        indices, test_size=args.val_size, stratify=labels, random_state=args.random_state
    )
    
    train_features = features[train_idx]
    train_labels = labels[train_idx]
    val_features = features[val_idx]
    val_labels = labels[val_idx]
    
    logging.info(f"Training samples: {len(train_labels)}, Validation samples: {len(val_labels)}")
    
    # Create PyTorch datasets and loaders
    train_dataset = FeaturesDataset(train_features, train_labels)
    val_dataset = FeaturesDataset(val_features, val_labels)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Determine input dimension (should be 770)
    input_dim = features.shape[1]
    logging.info(f"Input feature dimension: {input_dim}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")
    
    # Initialize model, criterion, and optimizer
    model = DistressClassifier(input_dim=input_dim)
    model.to(device)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
    
    best_val_f1 = 0.0
    best_epoch = 0
    
    # Training loop
    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        
        for batch_features, batch_labels in train_loader:
            batch_features, batch_labels = batch_features.to(device), batch_labels.to(device)
            optimizer.zero_grad()
            outputs = model(batch_features).squeeze(1)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * batch_features.size(0)
        
        avg_train_loss = running_loss / len(train_loader.dataset)
        val_loss, val_acc, val_f1 = evaluate(model, val_loader, device)
        
        logging.info(f"Epoch {epoch}: Train Loss = {avg_train_loss:.4f}, Val Loss = {val_loss:.4f}, Val Acc = {val_acc:.4f}, Val F1 = {val_f1:.4f}")
        
        # Save best model based on validation F1
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            os.makedirs(args.model_dir, exist_ok=True)
            model_path = os.path.join(args.model_dir, "best_model.pth")
            torch.save(model.state_dict(), model_path)
            logging.info(f"Saved best model at epoch {epoch} with Val F1 = {val_f1:.4f}")
    
    logging.info(f"Training complete. Best F1: {best_val_f1:.4f} at epoch {best_epoch}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a distress detection classifier using BERT embeddings and engineered features.")
    parser.add_argument("--features_path", type=str, default="data/processed/features/features.npy", help="Path to the combined features .npy file.")
    parser.add_argument("--labels_path", type=str, default="data/processed/features/labels.npy", help="Path to the combined labels .npy file.")
    parser.add_argument("--model_dir", type=str, default="models", help="Directory to save the trained model.")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=32, help="Training batch size.")
    parser.add_argument("--learning_rate", type=float, default=1e-4, help="Learning rate for the optimizer.")
    parser.add_argument("--val_size", type=float, default=0.2, help="Fraction of data to reserve for validation.")
    parser.add_argument("--random_state", type=int, default=42, help="Random state for reproducibility.")
    args = parser.parse_args()
    
    train_model(args)
