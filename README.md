# distress-detector
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
```
distress-detector/
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
```

## License
MIT License - see [LICENSE](LICENSE) for details

## Citation
```bibtex
@mastersthesis{AmnaZafar2025,
  title={distress-detector},
  author={Amna Zafar},
  year={2025},
  school={Your University}  # Replace with your university
}
```
