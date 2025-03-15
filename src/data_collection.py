import os
import praw
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Loaded environment variables from .env")

# Initialize Reddit API (official)
try:
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT'),
        check_for_async=False
    )
    logger.info("Initialized Reddit API client")
    logger.debug(f"Reddit client configuration: "
                 f"Client ID={os.getenv('REDDIT_CLIENT_ID')}, "
                 f"User Agent={os.getenv('REDDIT_USER_AGENT')}")
except Exception as e:
    logger.error(f"Failed to initialize Reddit API: {str(e)}", exc_info=True)
    raise

def collect_posts(subreddit, limit=1000):
    """
    Collect recent posts from a single subreddit (last 7 days)
    
    Args:
        subreddit: Subreddit name
        limit: Max number of posts
    
    Returns:
        DataFrame with collected posts
    """
    data = []
    try:
        subreddit_instance = reddit.subreddit(subreddit)
        logger.info(f"Starting collection for {subreddit}")
        
        for post in subreddit_instance.new(limit=limit):
            data.append({
                'id': post.id,
                'title': post.title,
                'text': post.selftext,
                'created_utc': datetime.utcfromtimestamp(post.created_utc),
                'author': post.author.name if post.author else '[deleted]',
                'subreddit': subreddit,
                'num_comments': post.num_comments,
                'score': post.score
            })
        
        logger.info(f"Collected {len(data)} posts from {subreddit}")
        return pd.DataFrame(data)
    
    except Exception as e:
        logger.error(f"Error collecting {subreddit}: {str(e)}", exc_info=True)
        return pd.DataFrame()

if __name__ == '__main__':
    logger.info("Starting data collection script execution")
    
    # Configuration
    SUBREDDITS = [
    "AskReddit",
    "ShowerThoughts",
    "NoStupidQuestions",
    "ExplainLikeImFive",
    "LifeProTips",
    "DoesAnybodyElse",
    "TooAfraidToAsk",
    "Confession",
    "AmITheAsshole",
    "Relationships",
    "memes",
    "dankmemes",
    "MemeEconomy",
    "wholesomememes",
    "AdviceAnimals",
    "HistoryMemes",
    "terriblefacebookmemes",
    "ComedyCemetery",
    "PrequelMemes",
    "BoneAppleTea",
    "gaming",
    "pcmasterrace",
    "consolewars",
    "leagueoflegends",
    "FortNiteBR",
    "Minecraft",
    "Steam",
    "speedrun",
    "esports",
    "Games",
    "science",
    "technology",
    "space",
    "askscience",
    "futurology",
    "Physics",
    "Biology",
    "Engineering",
    "Cyberpunk",
    "coolgithub",
    "news",
    "politics",
    "worldnews",
    "conspiracy",
    "TrueReddit",
    "geopolitics",
    "LateStageCapitalism",
    "PoliticalDiscussion",
    "moderatepolitics",
    "offbeat",
    "DIY",
    "LifeHacks",
    "Cooking",
    "Baking",
    "woodworking",
    "crochet",
    "knitting",
    "gardening",
    "photography",
    "art",
    "movies",
    "television",
    "netflixbestof",
    "anime",
    "HarryPotter",
    "GameOfThrones",
    "starwars",
    "lotrmemes",
    "MarvelStudios",
    "DC_Cinematic",
    "fitness",
    "running",
    "bodyweightfitness",
    "MealPrepSunday",
    "loseit",
    "mentalhealth",
    "selfimprovement",
    "getdisciplined",
    "minimalism",
    "frugal",
    "personalfinance",
    "investing",
    "financialindependence",
    "stocks",
    "CryptoCurrency",
    "wallstreetbets",
    "entrepreneur",
    "smallbusiness",
    "startups",
    "tax",
    "aww",
    "natureisfuckinglit",
    "EarthPorn",
    "nononono",
    "oddlysatisfying",
    "interestingasfuck",
    "blackmagicfuckery",
    "holdmybeer",
    "Unexpected",
    "nextfuckinglevel"]
    LIMIT = 1000  # Reddit allows up to 1000 posts per request
    
    # Process each subreddit individually
    for subreddit in tqdm(SUBREDDITS, desc='Subreddits'):
        try:
            df = collect_posts(subreddit, LIMIT)
            
            if not df.empty:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_filename = f"data/raw/{subreddit}_reddit_posts_{timestamp}"
                
                # Save to CSV
                csv_path = f"{base_filename}.csv"
                df.to_csv(csv_path, index=False)
                logger.info(f"Saved CSV: {csv_path} ({len(df)} posts)")
                
                # Save to JSON
                json_path = f"{base_filename}.json"
                df.to_json(json_path, orient='records')
                logger.info(f"Saved JSON: {json_path} ({len(df)} posts)")
                
            else:
                logger.warning(f"No posts collected for {subreddit}")
                
        except Exception as e:
            logger.error(f"Failed to process {subreddit}: {str(e)}", exc_info=True)
    
    logger.info("Script execution completed")