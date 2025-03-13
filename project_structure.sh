#!/bin/bash

# Create core directories
mkdir -p {src/{data_collection,preprocessing,models,visualization},data/{raw,processed,external},notebooks,models/{checkpoints,logs},results,docs,tests}

# Create root files
touch .gitignore requirements.txt Makefile

# Create .gitignore
cat <<EOL > .gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.ipynb_checkpoints
.DS_Store

# Data
data/raw/*
data/processed/*
data/external/*

# Models
models/checkpoints/*
models/logs/*

# Environment
.env
EOL

# Create requirements.txt
cat <<EOL > requirements.txt
pandas>=2.0
numpy>=1.24
transformers>=4.30
torch>=2.0
praw>=7.6.0
scikit-learn>=1.3
matplotlib>=3.7
EOL

# Create Makefile
cat <<EOL > Makefile
# Project workflows
data:
\tpython src/data_collection/reddit_scraper.py

preprocess:
\tpython src/preprocessing/text_processor.py

train:
\tpython src/models/train_multimodal.py

results:
\tpython src/visualization/plot_results.py

clean:
\trm -rf data/processed/* models/checkpoints/*
EOL

# Create source files
touch src/data_collection/{reddit_scraper.py,preprocess_raw.py}
touch src/preprocessing/{text_processor.py,feature_engineer.py}
touch src/models/{multimodal_model.py,train.py}
touch src/visualization/{plot_sentiment.py,plot_confusion.py}

# Create notebook templates
touch notebooks/{EDA.ipynb,baseline_text_only.ipynb,multimodal_analysis.ipynb}

# Create documentation files
cat <<EOL > docs/methodology.md
# Methodology

## Multimodal Approach
1. **Text Analysis**: BERT embeddings + sentiment analysis
2. **Behavioral Features**: Posting frequency, late-night activity
3. **Metadata**: Subreddit risk scores, user tenure
EOL

cat <<EOL > docs/ethics.md
# Ethical Considerations

1. **Anonymization**: All user data stripped of PII
2. **Bias Mitigation**: Regular audits across demographics
3. **Transparency**: Explainable predictions for flagged content
EOL