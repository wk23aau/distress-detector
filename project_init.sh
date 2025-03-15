#!/bin/bash

# Project Setup Script
PROJECT_NAME="distress-detector"
AUTHOR="Amna Zafar"
YEAR=$(date +%Y)

# Create directory structure
mkdir -p $PROJECT_NAME/{data/{raw,processed,annotations},src,experiments/{logs,checkpoints},results/{figures,tables},reports,docs}

# Create core files
touch $PROJECT_NAME/README.md
touch $PROJECT_NAME/LICENSE
touch $PROJECT_NAME/requirements.txt

# Create Python source files
touch $PROJECT_NAME/src/{data_collection.py,preprocessing.py,mentalbert_finetune.py,model_architecture.py,evaluate.py}

# Create documentation files
touch $PROJECT_NAME/docs/{methodology.md,ethical_compliance.md,reproducibility.md}

# Create experiment configuration
cat <<EOL > $PROJECT_NAME/experiments/config.yaml
# Training Configuration
random_seed: 42
batch_size: 16
learning_rate: 2e-5
epochs: 5
model_name: "mentalbert-base"
EOL

# Create initial README content
cat <<EOL > $PROJECT_NAME/README.md
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
├── data/          # Raw and processed datasets
├── src/           # Python source code
├── experiments/   # Training configurations and logs
└── ...
\`\`\`

## License
MIT License - see [LICENSE](LICENSE) for details

## Citation
\`\`\`bibtex
@mastersthesis{${AUTHOR// /}${YEAR},
  title={$PROJECT_NAME},
  author={$AUTHOR},
  year={$YEAR},
  school={Your University}
}
\`\`\`
EOL

# Create .gitignore
cat <<EOL > $PROJECT_NAME/.gitignore
# Data
data/raw/*
data/processed/*
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

# Secrets
.env
EOL

# Create LICENSE file (MIT)
cat <<EOL > $PROJECT_NAME/LICENSE
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

echo "Project '$PROJECT_NAME' initialized successfully!"
echo "Directory structure created at: $(pwd)/$PROJECT_NAME"