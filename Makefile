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
