# Multimodal Emotional Distress Detection on Reddit  
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)  
![GitHub](https://img.shields.io/badge/GitHub-Repo-green)  
![License](https://img.shields.io/badge/License-MIT-yellow)  

## Project Overview  
This research project develops an **AI-driven system** to detect emotional distress signals on Reddit using a **multimodal approach** (text, images, and user engagement patterns). By analyzing posts from mental health-focused subreddits (e.g., r/TrueOffMyChest), the system identifies early signs of distress through:  
- **NLP-based sentiment analysis** (BERT/RoBERTa)  
- **Computer vision** for facial emotion detection in images/GIFs  
- **Behavioral tracking** (post frequency, engagement metrics)  

### Key Objectives  
1. **Real-time monitoring** of Reddit content  
2. **Multimodal fusion** of text and visual data  
3. **Ethical AI implementation** with privacy safeguards  

---

## Dataset  
The dataset contains **10,000 Reddit posts** 
- **Access**: [GitHub Dataset Repository](https://github.com/wk23aau/distress-detector/tree/main/data/raw/reddit-posts)  
- **Composition**:  
  - Text posts (`title`, `selftext`)  
  - Image URLs (thumbnails, uploads)  
  - Metadata (`subreddit`, `created_utc`, `score`, `num_comments`)  
  - Flair tags (`link_flair_text`, `author_flair_text`)  

---

## Installation  
1. **Clone the repository**:  
   ```bash  
   git clone https://github.com/wk23aau/distress-detector.git  
   cd distress-detector

2. **Set up Python environment** :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. **Install dependencies** :
   ```bash
   pip install -r requirements.txt 
   ```
4. **Configure API keys** :
     Create a .env file with:
```bash
  REDDIT_CLIENT_ID=your_client_id  
  REDDIT_CLIENT_SECRET=your_client_secret  
  REDDIT_USERNAME=your_username  
  REDDIT_PASSWORD=your_password  
  GITHUB_TOKEN=your_github_token
   ```
---
## Usage
1. **Data Collection** :
```bash
python reddit_scraper.py --subreddit TrueOffMyChest --limit 10000 --batch-size 100
``` 
- Scrapes posts in batches (default: 100 posts/batch)
- Stores cleaned JSON data in data/raw/reddit-posts/
2. **Text Analysis**
```python
from analysis.text_analysis import analyze_sentiment  
analyze_sentiment("data/raw/reddit-posts/TrueOffMyChest_1-1000_2024-01-20.json")  
```
- Uses BERT for sentiment classification
- Extracts distress keywords and phrases
3. **Image Analysis**
```python
from analysis.image_analysis import detect_emotions_in_images  
detect_emotions_in_images("data/raw/reddit-posts/TrueOffMyChest_1-1000_2024-01-20.json")  
```
- Leverages OpenCV and DeepFace for facial emotion detection
---
## Project Structure
```bash
distress-detector/  
├── data/  
│   ├── raw/            # Raw scraped Reddit JSON files  
│   └── processed/      # Cleaned and analyzed data  
├── src/  
│   ├── reddit_scraper.py   # Data collection script  
│   ├── text_analysis.py    # NLP and sentiment analysis  
│   └── image_analysis.py   # Computer vision pipeline  
├── models/  
│   ├── bert_model/     # Fine-tuned NLP model  
│   └── cv_model/       # Trained computer vision model  
├── notebooks/          # Jupyter notebooks for experimentation  
└── requirements.txt    # Python dependencies  
```
## Ethical Considerations
**Anonymization** : All user identifiers (e.g., author) are removed during preprocessing
**Compliance** : Adheres to Reddit's API terms and GDPR/CCPA guidelines
**Transparency** : Model decisions are logged with explainability reports

## Contributing
- Fork the repository
- Create a feature branch (git checkout -b feature/YourFeature)
- Commit changes (git commit -m "Add feature")
- Push to GitHub (git push origin feature/YourFeature)
- Submit a pull request
## License
This project is licensed under the MIT License . See LICENSE for details.

## Contact
- Research Lead : Amna Zafar (amna.zafar@herts.ac.uk )
- GitHub Issues : Project Issues
