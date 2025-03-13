import os
import json
import time
from datetime import datetime
import pandas as pd
import praw
from dotenv import load_dotenv
from prawcore.exceptions import NotFound, Forbidden, TooManyRequests

# Load environment variables
load_dotenv()

def setup_reddit():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent="moderator_activity_analyzer by u/khanrazawaseem"
    )

def get_all_moderator_usernames():
    usernames = set()
    for file in os.listdir("data/raw/moderators"):
        if file.endswith(".json"):
            with open(f"data/raw/moderators/{file}", "r") as f:
                moderators = json.load(f)
                for mod in moderators:
                    usernames.add(mod['username'])
    return sorted(usernames)

def collect_posts_and_comments(reddit, username, post_limit, comment_limit):
    try:
        mod = reddit.redditor(username)
        posts = []
        comments = []
        
        # Collect posts with limit
        for post in mod.submissions.new(limit=post_limit):
            posts.append({
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'subreddit': post.subreddit.display_name,
                'created_utc': post.created_utc,
                'num_comments': post.num_comments,
                'score': post.score
            })
        
        # Collect comments with limit
        for comment in mod.comments.new(limit=comment_limit):
            comments.append({
                'id': comment.id,
                'body': comment.body,
                'post_id': comment.link_id.split('_')[1],
                'subreddit': comment.subreddit.display_name,
                'created_utc': comment.created_utc,
                'score': comment.score
            })
        
        return posts, comments
    except NotFound:
        print(f"Moderator {username} not found")
        return [], []
    except Forbidden:
        print(f"Private account: {username}")
        return [], []
    except TooManyRequests:
        print("Rate limit exceeded. Pausing for 60 seconds...")
        time.sleep(60)
        return collect_posts_and_comments(reddit, username, post_limit, comment_limit)
    except Exception as e:
        print(f"Error processing {username}: {str(e)}")
        return [], []

def get_total_activity_counts(reddit, username):
    """Get total post/comment counts using official API"""
    try:
        redditor = reddit.redditor(username)
        post_count = sum(1 for _ in redditor.submissions.new(limit=None))
        comment_count = sum(1 for _ in redditor.comments.new(limit=None))
        return post_count, comment_count
    except NotFound:
        return None, None
    except Forbidden:
        return None, None
    except Exception as e:
        print(f"Error getting totals for {username}: {str(e)}")
        return None, None

def save_data(username, posts, comments):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"data/raw/moderator-posts/{username}"
    os.makedirs(base_path, exist_ok=True)
    
    # Save posts
    if posts:
        df_posts = pd.DataFrame(posts)
        df_posts.to_csv(
            f"{base_path}/posts_{len(posts)}_{timestamp}.csv",
            index=False
        )
        with open(f"{base_path}/posts_{len(posts)}_{timestamp}.json", "w") as f:
            json.dump(posts, f, indent=2)
    
    # Save comments
    if comments:
        df_comments = pd.DataFrame(comments)
        df_comments.to_csv(
            f"{base_path}/comments_{len(comments)}_{timestamp}.csv",
            index=False
        )
        with open(f"{base_path}/comments_{len(comments)}_{timestamp}.json", "w") as f:
            json.dump(comments, f, indent=2)

def get_user_input(prompt, default=None):
    while True:
        value = input(prompt)
        if not value:
            return default() if callable(default) else default
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid number or leave blank for default")

def main():
    reddit = setup_reddit()
    all_usernames = get_all_moderator_usernames()
    
    # Get user inputs
    max_mods = len(all_usernames)
    mod_count = get_user_input(
        f"Enter number of moderators to process (max {max_mods}): ",
        default=lambda: max_mods
    )
    
    post_limit = get_user_input(
        "Enter maximum posts per moderator (default: 1000): ",
        default=1000
    )
    
    comment_limit = get_user_input(
        "Enter maximum comments per moderator (default: 1000): ",
        default=1000
    )
    
    selected = all_usernames[:mod_count]
    print(f"\nProcessing {len(selected)} moderators...\n")

    for username in selected:
        print(f"{'='*40}")
        print(f"Processing moderator: {username}")
        print(f"{'='*40}")
        
        # Collect recent activity
        posts, comments = collect_posts_and_comments(
            reddit, username, post_limit, comment_limit
        )
        
        # Save data
        save_data(username, posts, comments)
        print(f"\nSaved {len(posts)} posts and {len(comments)} comments")
        
        # Get total activity counts
        print("Calculating total activity (this may take a few moments)...")
        total_posts, total_comments = get_total_activity_counts(reddit, username)
        
        # Display summary
        print("\n--- Activity Summary ---")
        if total_posts is not None and total_comments is not None:
            print(f"Total Posts: {total_posts}")
            print(f"Total Comments: {total_comments}")
        else:
            print("Could not retrieve total activity counts")
        
        # Rate limit handling
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Critical error: {str(e)}")