import os
import time
import json
from datetime import datetime
import pandas as pd
import praw
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_reddit():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent="moderator_scraper by u/khanrazawaseem"
    )

def save_subreddits(data, start, end):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{start}_{end}_{timestamp}"
    os.makedirs("data/raw/subreddit-ids", exist_ok=True)
    
    # Save as CSV
    df = pd.DataFrame(data)
    df.to_csv(f"data/raw/subreddit-ids/{filename}.csv", index=False)
    
    # Save as JSON
    with open(f"data/raw/subreddit-ids/{filename}.json", "w") as f:
        json.dump(data, f, indent=2)

def save_moderators(subreddit_id, moderators):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data/raw/moderators", exist_ok=True)
    filename = f"{subreddit_id}_moderators_{timestamp}.json"
    
    with open(f"data/raw/moderators/{filename}", "w") as f:
        json.dump(moderators, f, indent=2)

def get_subreddits_and_moderators(limit):
    reddit = setup_reddit()
    subreddits = []
    
    for i in range(0, limit, 100):
        print(f"Fetching subreddit batch starting at {i}...")
        subs = reddit.subreddits.popular(limit=100, params={'after': i})
        
        for sub in subs:
            # Collect subreddit data
            subreddit_data = {
                'id': sub.id,
                'name': sub.display_name,
                'title': sub.title,
                'subscribers': sub.subscribers
            }
            subreddits.append(subreddit_data)
            
            # Collect moderators
            moderators = []
            try:
                for moderator in sub.moderator():
                    moderators.append({
                        'username': moderator.name,
                        'id': moderator.id,
                        'mod_permissions': list(moderator.mod_permissions)
                    })
                save_moderators(sub.id, moderators)
                print(f"Saved {len(moderators)} moderators for r/{sub.display_name}")
            except Exception as e:
                print(f"Error fetching moderators for r/{sub.display_name}: {str(e)}")
            
            time.sleep(1)  # Rate limit between subreddits
        
        time.sleep(2)  # Rate limit between batches
    
    return subreddits[:limit]

if __name__ == "__main__":
    try:
        limit = int(input("Enter number of subreddit IDs to collect: "))
        print(f"Collecting {limit} subreddits with moderator data...")
        
        subreddits = get_subreddits_and_moderators(limit)
        save_subreddits(subreddits, 0, len(subreddits))
        
        print(f"Successfully saved {len(subreddits)} subreddits to:")
        print(f"data/raw/subreddit-ids/0_{len(subreddits)}_*.csv/json")
        print("Moderator data saved to data/raw/moderators/")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check your credentials and try again.")