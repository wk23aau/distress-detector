import os
import json
import time
from datetime import datetime
import praw
from dotenv import load_dotenv
from prawcore.exceptions import NotFound, Forbidden, TooManyRequests
from tqdm import tqdm
import pandas as pd

# Load environment variables
load_dotenv()

def setup_reddit():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent="moderator_activity_collector by u/khanrazawaseem"
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

def get_all_subreddits():
    subreddits = set()
    for file in os.listdir("data/raw/subreddits"):
        if file.endswith(".json"):
            with open(f"data/raw/subreddits/{file}", "r") as f:
                data = json.load(f)
                for item in data:
                    subreddits.add(item['name'])
        elif file.endswith(".csv"):
            df = pd.read_csv(f"data/raw/subreddits/{file}")
            subreddits.update(df['name'].tolist())
    return sorted(subreddits)

def get_all_users():
    users = set()
    for file in os.listdir("data/raw/users"):
        if file.endswith(".json"):
            with open(f"data/raw/users/{file}", "r") as f:
                data = json.load(f)
                for item in data:
                    users.add(item['username'])
        elif file.endswith(".csv"):
            df = pd.read_csv(f"data/raw/users/{file}")
            users.update(df['username'].tolist())
    return sorted(users)

def collect_posts_and_comments(reddit, username, post_limit=None, comment_limit=None):
    try:
        user = reddit.redditor(username)
        posts = []
        user_comments = []
        
        # Collect posts
        post_query = user.submissions.new(limit=post_limit)
        for post in tqdm(post_query, desc=f"Posts [{username}]", unit="post", leave=False):
            try:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'selftext': post.selftext,
                    'url': post.url,
                    'subreddit': post.subreddit.display_name,
                    'created_utc': post.created_utc,
                    'author': post.author.name if post.author else "[deleted]",
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'comments': []
                }
                
                # Collect comments on the post
                post.comments.replace_more(limit=comment_limit)
                for comment in post.comments.list():
                    comment_data = {
                        'id': comment.id,
                        'body': comment.body,
                        'created_utc': comment.created_utc,
                        'author': comment.author.name if comment.author else "[deleted]",
                        'score': comment.score,
                        'parent_id': comment.parent_id,
                        'permalink': comment.permalink
                    }
                    post_data['comments'].append(comment_data)
                
                posts.append(post_data)
            except Exception as e:
                tqdm.write(f"Error processing post {post.id}: {str(e)}")
        
        # Collect user's own comments
        comment_query = user.comments.new(limit=comment_limit)
        for comment in tqdm(comment_query, desc=f"Comments [{username}]", unit="comment", leave=False):
            try:
                comment_data = {
                    'id': comment.id,
                    'body': comment.body,
                    'created_utc': comment.created_utc,
                    'author': comment.author.name if comment.author else "[deleted]",
                    'score': comment.score,
                    'parent_id': comment.parent_id,
                    'permalink': comment.permalink
                }
                user_comments.append(comment_data)
            except Exception as e:
                tqdm.write(f"Error processing comment {comment.id}: {str(e)}")
        
        return posts, user_comments
    
    except NotFound:
        tqdm.write(f"User {username} not found")
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

def save_data(username, posts, comments, user_type='moderator'):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"data/raw/{user_type}s/{username}"
    os.makedirs(base_path, exist_ok=True)
    
    if posts:
        with open(f"{base_path}/posts_full_{len(posts)}_{timestamp}.json", "w") as f:
            json.dump(posts, f, indent=2)
        posts_csv = [{
            'id': p['id'],
            'title': p['title'],
            'subreddit': p['subreddit'],
            'created_utc': p['created_utc'],
            'score': p['score'],
            'num_comments': p['num_comments']
        } for p in posts]
        pd.DataFrame(posts_csv).to_csv(
            f"{base_path}/posts_summary_{len(posts)}_{timestamp}.csv",
            index=False
        )
    
    if comments:
        with open(f"{base_path}/comments_full_{len(comments)}_{timestamp}.json", "w") as f:
            json.dump(comments, f, indent=2)
        comments_csv = [{
            'id': c['id'],
            'body': c['body'],
            'subreddit': c['subreddit'],
            'created_utc': c['created_utc'],
            'score': c['score']
        } for c in comments]
        pd.DataFrame(comments_csv).to_csv(
            f"{base_path}/comments_summary_{len(comments)}_{timestamp}.csv",
            index=False
        )

def save_subreddit_data(subreddit_name, posts_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"data/raw/subreddits/{subreddit_name}"
    os.makedirs(base_path, exist_ok=True)
    
    with open(f"{base_path}/posts_full_{len(posts_data)}_{timestamp}.json", "w") as f:
        json.dump(posts_data, f, indent=2)
    
    posts_csv = [{
        'id': p['id'],
        'title': p['title'],
        'subreddit': p['subreddit'],
        'created_utc': p['created_utc'],
        'score': p['score'],
        'num_comments': p['num_comments']
    } for p in posts_data]
    pd.DataFrame(posts_csv).to_csv(
        f"{base_path}/posts_summary_{len(posts_data)}_{timestamp}.csv",
        index=False
    )

def get_user_input(prompt, default=None):
    while True:
        value = input(prompt)
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid number or leave blank for default")

def process_subreddits(reddit):
    subreddits = get_all_subreddits()
    if not subreddits:
        print("No subreddits found in data/raw/subreddits")
        return
    
    max_subs = len(subreddits)
    sub_count = get_user_input(
        f"Enter number of subreddits to process (max {max_subs}): ",
        default=max_subs
    )
    post_limit = get_user_input(
        "Enter maximum posts per subreddit (leave blank to collect ALL): ",
        default=None
    )
    comment_limit = get_user_input(
        "Enter maximum comments per post (leave blank to collect ALL): ",
        default=None
    )
    
    selected = subreddits[:sub_count]
    
    for subreddit_name in tqdm(selected, desc="Processing Subreddits", unit="subreddit"):
        collect_subreddit_data(reddit, subreddit_name, post_limit, comment_limit)
        time.sleep(5)

def collect_subreddit_data(reddit, subreddit_name, post_limit=None, comment_limit=None):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        moderator_names = set(mod.name for mod in subreddit.moderator())
        non_mod_users = set()
        posts_data = []
        
        # Collect subreddit posts and comments
        post_query = subreddit.new(limit=post_limit)
        for post in tqdm(post_query, desc=f"Collecting posts from r/{subreddit_name}", unit="post"):
            try:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'selftext': post.selftext,
                    'url': post.url,
                    'subreddit': post.subreddit.display_name,
                    'created_utc': post.created_utc,
                    'author': post.author.name if post.author else "[deleted]",
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'comments': []
                }
                
                if post.author:
                    if post.author.name in moderator_names:
                        pass
                    else:
                        non_mod_users.add(post.author.name)
                
                post.comments.replace_more(limit=comment_limit)
                for comment in post.comments.list():
                    comment_data = {
                        'id': comment.id,
                        'body': comment.body,
                        'created_utc': comment.created_utc,
                        'author': comment.author.name if comment.author else "[deleted]",
                        'score': comment.score,
                        'parent_id': comment.parent_id,
                        'permalink': comment.permalink
                    }
                    post_data['comments'].append(comment_data)
                
                posts_data.append(post_data)
            except Exception as e:
                tqdm.write(f"Error processing post {post.id}: {str(e)}")
        
        save_subreddit_data(subreddit_name, posts_data)
        
        # Process moderators
        for mod_name in tqdm(moderator_names, desc=f"Processing moderators of r/{subreddit_name}"):
            posts, comments = collect_posts_and_comments(reddit, mod_name, post_limit, comment_limit)
            save_data(mod_name, posts, comments, user_type='moderator')
            time.sleep(5)
        
        # Process non-moderators
        for user_name in tqdm(non_mod_users, desc=f"Processing non-moderators in r/{subreddit_name}"):
            if user_name and user_name != "[deleted]":
                posts, comments = collect_posts_and_comments(reddit, user_name, post_limit, comment_limit)
                save_data(user_name, posts, comments, user_type='user')
                time.sleep(5)
        
    except Exception as e:
        tqdm.write(f"Error processing subreddit {subreddit_name}: {str(e)}")

def process_users(reddit):
    users = get_all_users()
    if not users:
        print("No users found in data/raw/users")
        return
    
    max_users = len(users)
    user_count = get_user_input(
        f"Enter number of users to process (max {max_users}): ",
        default=max_users
    )
    post_limit = get_user_input(
        "Enter maximum posts per user (leave blank to collect ALL): ",
        default=None
    )
    comment_limit = get_user_input(
        "Enter maximum comments per user (leave blank to collect ALL): ",
        default=None
    )
    
    selected = users[:user_count]
    
    for username in tqdm(selected, desc="Processing Users", unit="user"):
        posts, comments = collect_posts_and_comments(reddit, username, post_limit, comment_limit)
        save_data(username, posts, comments, user_type='user')
        time.sleep(5)

def process_moderators(reddit):
    moderators = get_all_moderator_usernames()
    if not moderators:
        print("No moderators found in data/raw/moderators")
        return
    
    max_mods = len(moderators)
    mod_count = get_user_input(
        f"Enter number of moderators to process (max {max_mods}): ",
        default=max_mods
    )
    post_limit = get_user_input(
        "Enter maximum posts per moderator (leave blank to collect ALL): ",
        default=None
    )
    comment_limit = get_user_input(
        "Enter maximum comments per moderator (leave blank to collect ALL): ",
        default=None
    )
    
    selected = moderators[:mod_count]
    
    for username in tqdm(selected, desc="Processing Moderators", unit="mod"):
        posts, comments = collect_posts_and_comments(reddit, username, post_limit, comment_limit)
        save_data(username, posts, comments, user_type='moderator')
        time.sleep(5)

def main():
    reddit = setup_reddit()
    input_type = input("Enter input type (s=subreddit, u=user, m=moderator): ").strip().lower()
    
    if input_type not in ['s', 'u', 'm']:
        print("Invalid input type. Please enter s, u, or m.")
        return
    
    if input_type == 's':
        process_subreddits(reddit)
    elif input_type == 'u':
        process_users(reddit)
    elif input_type == 'm':
        process_moderators(reddit)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        tqdm.write("\nProcess interrupted by user")
    except Exception as e:
        tqdm.write(f"Critical error: {str(e)}")