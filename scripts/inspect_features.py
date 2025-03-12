#!/usr/bin/env python3
"""
Inspect BERT Embeddings and Labels

This script loads the features and labels saved as NumPy arrays from the
data/processed/features directory, prints their shapes, and shows a few sample rows.
"""

import os
import argparse
import numpy as np

def main(features_path, labels_path, num_samples):
    # Load the features and labels
    features = np.load(features_path)
    labels = np.load(labels_path)
    
    print(f"Features shape: {features.shape}")
    print(f"Labels shape: {labels.shape}")
    
    # Display a few sample feature vectors and their labels
    print("\nSample feature vectors and corresponding labels:")
    for i in range(min(num_samples, features.shape[0])):
        print(f"Sample {i+1}:")
        print(f"Features (first 10 dims): {features[i][:10]} ...")
        print(f"Label: {labels[i]}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect saved BERT features and labels.")
    parser.add_argument("--features_path", type=str, default="data/processed/features/features.npy",
                        help="Path to the saved features .npy file.")
    parser.add_argument("--labels_path", type=str, default="data/processed/features/labels.npy",
                        help="Path to the saved labels .npy file.")
    parser.add_argument("--num_samples", type=int, default=5,
                        help="Number of samples to display.")
    args = parser.parse_args()
    
    main(args.features_path, args.labels_path, args.num_samples)
