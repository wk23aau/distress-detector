#!/bin/bash

# Exit on error
set -e

# Project name
PROJECT_NAME="distress-detector"

# Full path to Python (from 'which python')
PYTHON_PATH="/c/Program Files/Python312/python"

# Author and Year for LICENSE and README
AUTHOR="Amna Zafar"  # Or your name
YEAR=$(date +%Y)

# --- Create Directories ---
echo "Creating project directories..."
mkdir -p "$PROJECT_NAME"/{data/{raw,processed,external,interim,annotations},models,notebooks,src/{data,features,models,visualization,utils},reports/figures,docs,experiments/{logs,checkpoints}}

# --- Create Placeholder Files ---
echo "Creating placeholder files..."

# data/
touch "$PROJECT_NAME"/data/raw/.gitkeep
touch "$PROJECT_NAME"/data/processed/.gitkeep
touch "$PROJECT_NAME"/data/external/.gitkeep
touch "$PROJECT_NAME"/data/interim/.gitkeep
touch "$PROJECT_NAME"/data/annotations/.gitkeep


# models/
touch "$PROJECT_NAME"/models/.gitkeep

# notebooks/
touch "$PROJECT_NAME"/notebooks/example_notebook.ipynb

# src/
touch "$PROJECT_NAME"/src/data/make_dataset.py
touch "$PROJECT_NAME"/src/data/preprocess_text.py
touch "$PROJECT_NAME"/src/data/preprocess_image.py
touch "$PROJECT_NAME"/src/data/preprocess_activity.py
# New src files, merging previous suggestions
touch "$PROJECT_NAME"/src/features/build_features.py
touch "$PROJECT_NAME"/src/models/train_model.py
touch "$PROJECT_NAME"/src/models/predict_model.py
touch "$PROJECT_NAME"/src/models/model_architecture.py # Renamed from model.py
touch "$PROJECT_NAME"/src/models/utils.py
touch "$PROJECT_NAME"/src/models/mentalbert_finetune.py # Added for MentalBERT specific
touch "$PROJECT_NAME"/src/visualization/visualize.py
touch "$PROJECT_NAME"/src/utils/helpers.py
touch "$PROJECT_NAME"/src/evaluate.py  # For evaluation scripts


# reports/
touch "$PROJECT_NAME"/reports/figures/.gitkeep
touch "$PROJECT_NAME"/reports/final_report.md  # Keep the main report file

# docs/ (for documentation, as per the new script)
touch "$PROJECT_NAME"/docs/methodology.md
touch "$PROJECT_NAME"/docs/ethical_compliance.md
touch "$PROJECT_NAME"/docs/reproducibility.md

# experiments/
touch "$PROJECT_NAME"/experiments/logs/.gitkeep
touch "$PROJECT_NAME"/experiments/checkpoints/.gitkeep
touch "$PROJECT_NAME"/experiments/config.yaml #Keep the config

# config/  <- Remove config directory. config.yaml is in experiments.

# --- Create Core Files ---
touch "$PROJECT_NAME"/README.md
touch "$PROJECT_NAME"/LICENSE
touch "$PROJECT_NAME"/requirements.txt
touch "$PROJECT_NAME"/.gitignore

# --- Populate Files ---

# Create experiment configuration (config.yaml)
cat <<EOL > "$PROJECT_NAME"/experiments/config.yaml
# Training Configuration
random_seed: 42
batch_size: 16
learning_rate: 2e-5
epochs: 5
model_name: "mentalbert-base"  # Or your preferred model
EOL

# Create initial README content
cat <<EOL > "$PROJECT_NAME"/README.md
# $PROJECT_NAME
Multimodal AI Approach to Emotional Distress Detection on Reddit

## Overview
This project implements a multimodal framework combining text analysis (MentalBERT) with metadata features to detect emotional distress in Reddit posts.

## Features
- MentalBERT fine-tuning for distress classification
- Multimodal fusion architecture
- Ethical data handling compliant with GDPR

## Requirements
- Python 3.8+
- PyTorch, Transformers, Scikit-learn

## Directory Structure
\`\`\`
${PROJECT_NAME}/
├── data/          # Raw, processed, and annotation datasets
│   ├── raw/       # Original, immutable data
│   ├── processed/ # Data after cleaning, preprocessing
│   ├── external/  # Data from third-party sources (if any)
│   ├── interim/   # Intermediate data files
│   └── annotations/ # Annotation files
├── models/        # Trained models, checkpoints
├── notebooks/     # Jupyter notebooks for EDA and experimentation
├── src/           # Source code
│   ├── data/      # Scripts for data handling
│   │   ├── make_dataset.py
│   │   ├── preprocess_text.py
│   │   ├── preprocess_image.py
│   │   └── preprocess_activity.py
│   ├── features/  # Scripts for feature engineering
│   │   └── build_features.py
│   ├── models/    # Model definition, training, prediction
│   │   ├── train_model.py
│   │   ├── predict_model.py
│   │   ├── model_architecture.py
│   │   ├── utils.py
│   │   └── mentalbert_finetune.py
│   ├── visualization/ # Scripts for creating visualizations
│   │   └── visualize.py
│   └── utils/     # General utility functions
│       └── helpers.py
├── reports/       # Report figures, tables, final report
│   ├── figures/
│   └── final_report.md
├── docs/          # Documentation files
│   ├── methodology.md
│   ├── ethical_compliance.md
│   └── reproducibility.md
├── experiments/   # Training configurations, logs, checkpoints
│   ├── logs/
│   ├── checkpoints/
│   └── config.yaml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
\`\`\`

## License
MIT License - see [LICENSE](LICENSE) for details

## Citation
\`\`\`bibtex
@mastersthesis{${AUTHOR// /}${YEAR},
  title={$PROJECT_NAME},
  author={$AUTHOR},
  year={$YEAR},
  school={Your University}  # Replace with your university
}
\`\`\`
EOL

# Create .gitignore
cat <<EOL > "$PROJECT_NAME"/.gitignore
# Data
data/raw/*
data/processed/*
data/interim/*
data/external/*
data/annotations/*

# Checkpoints
experiments/checkpoints/*

# Logs
experiments/logs/*

# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Jupyter
.ipynb_checkpoints

# System
.DS_Store
Thumbs.db

# Models
models/*

# Secrets / Environment
.env
EOL

# Create LICENSE file (MIT)
cat <<EOL > "$PROJECT_NAME"/LICENSE
MIT License

Copyright (c) $YEAR $AUTHOR

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOL

# --- Virtual Environment Setup ---
echo "Setting up virtual environment..."
if ! command -v "$PYTHON_PATH" &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

if ! command -v virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    "$PYTHON_PATH" -m pip install --user virtualenv
fi

#"$PROJECT_NAME"  <--  Commented out
"$PYTHON_PATH" -m venv .venv

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Print next steps
echo "Project '$PROJECT_NAME' initialized successfully!"
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo "Place your raw data in the data/raw directory."
echo "You can now start working on your project.  See README.md for more information."

#cd .. <-- Commented out