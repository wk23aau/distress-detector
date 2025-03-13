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

def collect_posts_and_comments(reddit, username, post_limit=None, comment_limit=None):
    try:
        mod = reddit.redditor(username)
        posts = []
        mod_comments = []
        
        # Collect posts with nested comments from others
        for post in mod.submissions.new(limit=post_limit):
            # Process post data
            post_data = {
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'subreddit': post.subreddit.display_name,
                'created_utc': post.created_utc,
                'num_comments': post.num_comments,
                'score': post.score,
                'comments': []  # Nested comments from others
            }
            
            # Fetch and process comments on this post
            try:
                post.comments.replace_more(limit=None)  # Load all comments
                for comment in post.comments.list():
                    if comment.author and comment.author.name != username:
                        # Collect comment data
                        comment_data = {
                            'id': comment.id,
                            'author': comment.author.name,
                            'body': comment.body,
                            'created_utc': comment.created_utc,
                            'score': comment.score,
                            'post_id': post.id
                        }
                        post_data['comments'].append(comment_data)
            except Exception as e:
                print(f"Error processing comments for post {post.id}: {str(e)}")
            
            posts.append(post_data)
        
        # Collect moderator's own comments
        for comment in mod.comments.new(limit=comment_limit):
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

def save_data(username, posts, mod_comments):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"data/raw/moderator-posts/{username}"
    os.makedirs(base_path, exist_ok=True)
    
    # Save posts with nested comments (JSON only)
    if posts is not None:
        # Save full data with comments to JSON
        with open(f"{base_path}/posts_with_comments_{len(posts)}_{timestamp}.json", "w") as f:
            json.dump(posts, f, indent=2)
        
        # Save simplified version to CSV (without nested comments)
        posts_csv = [{k: v for k, v in post.items() if k != 'comments'} for post in posts]
        df_posts = pd.DataFrame(posts_csv)
        df_posts.to_csv(
            f"{base_path}/posts_{len(posts)}_{timestamp}.csv",
            index=False
        )
    
    # Save moderator's own comments
    if mod_comments:
        df_comments = pd.DataFrame(mod_comments)
        df_comments.to_csv(
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
    
    # Get user inputs
    max_mods = len(all_usernames)
    mod_count = get_user_input(
        f"Enter number of moderators to process (max {max_mods}): ",
        default=max_mods
    )
    
    # Get limits (None = collect all)
    post_limit = get_user_input(
        "Enter maximum posts per moderator (leave blank to collect ALL): ",
        default=None
    )
    
    comment_limit = get_user_input(
        "Enter maximum comments per moderator (leave blank to collect ALL): ",
        default=None
    )
    
    selected = all_usernames[:mod_count]
    print(f"\nProcessing {len(selected)} moderators...\n")

    for username in selected:
        print(f"{'='*40}")
        print(f"Processing moderator: {username}")
        print(f"{'='*40}")
        
        # Collect data
        print(f"Collecting posts (limit: {post_limit or 'ALL'}) and comments (limit: {comment_limit or 'ALL'})")
        posts, mod_comments = collect_posts_and_comments(
            reddit, username, post_limit, comment_limit
        )
        
        # Save data
        save_data(username, posts, mod_comments)
        print(f"\nSaved {len(posts)} posts and {len(mod_comments)} moderator comments")
        print(f"Nested {sum(len(post['comments']) for post in posts)} comments from others on posts")
        
        # Rate limit handling
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Critical error: {str(e)}")