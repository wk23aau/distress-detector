import os
import json
import time
from datetime import datetime
import pandas as pd
import praw
from dotenv import load_dotenv
from prawcore.exceptions import NotFound, Forbidden, TooManyRequests
from tqdm import tqdm

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

def collect_posts_and_comments(reddit, username, post_limit=None, comment_limit=None):
    try:
        mod = reddit.redditor(username)
        posts = []
        mod_comments = []
        
        # Collect posts with progress bar
        post_query = mod.submissions.new(limit=post_limit)
        post_total = post_limit if post_limit is not None else 0
        for post in tqdm(
            post_query,
            desc=f"Posts for u/{username}",
            total=post_total,
            leave=False,
            dynamic_ncols=True
        ):
            post_data = {
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'subreddit': post.subreddit.display_name,
                'created_utc': post.created_utc,
                'num_comments': post.num_comments,
                'score': post.score,
                'comments': []
            }
            
            # Collect comments on post
            try:
                post.comments.replace_more(limit=None)
                comments = post.comments.list()
                for comment in tqdm(
                    comments,
                    desc=f"Comments for post {post.id}",
                    leave=False,
                    dynamic_ncols=True
                ):
                    if comment.author and comment.author.name != username:
                        post_data['comments'].append({
                            'id': comment.id,
                            'author': comment.author.name,
                            'body': comment.body,
                            'created_utc': comment.created_utc,
                            'score': comment.score,
                            'post_id': post.id
                        })
            except Exception as e:
                tqdm.write(f"Error processing comments for post {post.id}: {str(e)}")
            
            posts.append(post_data)
        
        # Collect moderator's own comments with progress bar
        comment_query = mod.comments.new(limit=comment_limit)
        comment_total = comment_limit if comment_limit is not None else 0
        for comment in tqdm(
            comment_query,
            desc=f"Mod comments for u/{username}",
            total=comment_total,
            leave=False,
            dynamic_ncols=True
        ):
            mod_comments.append({
                'id': comment.id,
                'body': comment.body,
                'post_id': comment.link_id.split('_')[1],
                'subreddit': comment.subreddit.display_name,
                'created_utc': comment.created_utc,
                'score': comment.score
            })
        
        return posts, mod_comments
    
    except NotFound:
        tqdm.write(f"Moderator {username} not found")
        return [], []
    except Forbidden:
        tqdm.write(f"Private account: {username}")
        return [], []
    except TooManyRequests:
        tqdm.write("Rate limit exceeded. Pausing for 60 seconds...")
        time.sleep(60)
        return collect_posts_and_comments(reddit, username, post_limit, comment_limit)
    except Exception as e:
        tqdm.write(f"Error processing {username}: {str(e)}")
        return [], []

def save_data(username, posts, mod_comments):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"data/raw/moderator-posts/{username}"
    os.makedirs(base_path, exist_ok=True)
    
    # Save posts with nested comments
    if posts:
        with open(f"{base_path}/posts_with_comments_{len(posts)}_{timestamp}.json", "w") as f:
            json.dump(posts, f, indent=2)
        
        posts_csv = [{k: v for k, v in post.items() if k != 'comments'} for post in posts]
        pd.DataFrame(posts_csv).to_csv(
            f"{base_path}/posts_{len(posts)}_{timestamp}.csv",
            index=False
        )
    
    # Save moderator's own comments
    if mod_comments:
        pd.DataFrame(mod_comments).to_csv(
            f"{base_path}/moderator_comments_{len(mod_comments)}_{timestamp}.csv",
            index=False
        )
        with open(f"{base_path}/moderator_comments_{len(mod_comments)}_{timestamp}.json", "w") as f:
            json.dump(mod_comments, f, indent=2)

def get_user_input(prompt, default=None):
    while True:
        value = input(prompt)
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid number or leave blank for default")

def main():
    reddit = setup_reddit()
    all_usernames = get_all_moderator_usernames()
    
    # Get user inputs with progress bar for input
    with tqdm(total=3, desc="User Input", leave=False) as pbar:
        max_mods = len(all_usernames)
        mod_count = get_user_input(
            f"Enter number of moderators to process (max {max_mods}): ",
            default=max_mods
        )
        pbar.update(1)
        
        post_limit = get_user_input(
            "Enter maximum posts per moderator (leave blank to collect ALL): ",
            default=None
        )
        pbar.update(1)
        
        comment_limit = get_user_input(
            "Enter maximum comments per moderator (leave blank to collect ALL): ",
            default=None
        )
        pbar.update(1)
    
    selected = all_usernames[:mod_count]
    
    # Process moderators with progress bar
    for username in tqdm(selected, desc="Processing Moderators", unit="mod"):
        posts, mod_comments = collect_posts_and_comments(
            reddit, username, post_limit, comment_limit
        )
        save_data(username, posts, mod_comments)
        time.sleep(5)  # Rate limiting

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        tqdm.write("\nProcess interrupted by user")
    except Exception as e:
        tqdm.write(f"Critical error: {str(e)}")