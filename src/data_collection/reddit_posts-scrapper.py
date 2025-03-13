import os
import json
import time
from datetime import datetime
import praw
from dotenv import load_dotenv
from prawcore.exceptions import NotFound, Forbidden, TooManyRequests
from tqdm import tqdm
import pandas as pd  # Added missing import for DataFrame

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

def collect_posts_and_comments(reddit, username, post_limit=None, comment_limit=None):
    try:
        mod = reddit.redditor(username)
        posts = []
        mod_comments = []
        
        # Collect posts with full metadata
        post_query = mod.submissions.new(limit=post_limit)
        for post in tqdm(
            post_query,
            desc=f"Posts [{username}]",
            unit="post",
            leave=False,
            dynamic_ncols=True
        ):
            try:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'selftext': post.selftext,
                    'url': post.url,
                    'subreddit': post.subreddit.display_name,
                    'created_utc': post.created_utc,
                    'author': post.author.name if post.author else "[deleted]",
                    'author_fullname': post.author.fullname if post.author else None,
                    'score': post.score,
                    'upvote_ratio': post.upvote_ratio,
                    'num_comments': post.num_comments,
                    'edited': post.edited,
                    'gilded': post.gilded,
                    'stickied': post.stickied,
                    'locked': post.locked,
                    'over_18': post.over_18,
                    'spoiler': post.spoiler,
                    'is_original_content': post.is_original_content,
                    'domain': post.domain,
                    'permalink': post.permalink,
                    'link_flair_text': getattr(post, 'link_flair_text', None),  # Added
                    'post_hint': getattr(post, 'post_hint', None),              # Added
                    'comments': []
                }
                
                # Collect comments on post with full metadata
                post.comments.replace_more(limit=None)
                for comment in post.comments.list():
                    if comment.author and comment.author.name != username:
                        comment_data = {
                            'id': comment.id,
                            'body': comment.body,
                            'body_html': comment.body_html,
                            'created_utc': comment.created_utc,
                            'author': comment.author.name if comment.author else "[deleted]",
                            'author_fullname': comment.author.fullname if comment.author else None,
                            'score': comment.score,
                            'parent_id': comment.parent_id,
                            'link_id': comment.link_id,
                            'gilded': comment.gilded,
                            'stickied': comment.stickied,
                            'edited': comment.edited,
                            'score_hidden': comment.score_hidden,
                            'subreddit': comment.subreddit.display_name,
                            'permalink': comment.permalink
                        }
                        post_data['comments'].append(comment_data)
                
                posts.append(post_data)
            except Exception as e:
                tqdm.write(f"Error processing post {post.id}: {str(e)}")
        
        # Collect moderator's own comments with full metadata
        comment_query = mod.comments.new(limit=comment_limit)
        for comment in tqdm(
            comment_query,
            desc=f"Mod Comments [{username}]",
            unit="comment",
            leave=False,
            dynamic_ncols=True
        ):
            try:
                mod_comments.append({
                    'id': comment.id,
                    'body': comment.body,
                    'body_html': comment.body_html,
                    'created_utc': comment.created_utc,
                    'author': comment.author.name if comment.author else "[deleted]",
                    'author_fullname': comment.author.fullname if comment.author else None,
                    'score': comment.score,
                    'parent_id': comment.parent_id,
                    'link_id': comment.link_id,
                    'gilded': comment.gilded,
                    'stickied': comment.stickied,
                    'edited': comment.edited,
                    'score_hidden': comment.score_hidden,
                    'subreddit': comment.subreddit.display_name,
                    'permalink': comment.permalink
                })
            except Exception as e:
                tqdm.write(f"Error processing comment {comment.id}: {str(e)}")
        
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
    
    # Save posts with all metadata
    if posts:
        with open(f"{base_path}/posts_full_{len(posts)}_{timestamp}.json", "w") as f:
            json.dump(posts, f, indent=2)
        
        # Save simplified CSV for quick reference
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
    
    # Save moderator's own comments
    if mod_comments:
        with open(f"{base_path}/mod_comments_full_{len(mod_comments)}_{timestamp}.json", "w") as f:
            json.dump(mod_comments, f, indent=2)
        
        # Save simplified CSV
        comments_csv = [{
            'id': c['id'],
            'body': c['body'],
            'subreddit': c['subreddit'],
            'created_utc': c['created_utc'],
            'score': c['score']
        } for c in mod_comments]
        pd.DataFrame(comments_csv).to_csv(
            f"{base_path}/mod_comments_summary_{len(mod_comments)}_{timestamp}.csv",
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

def main():
    reddit = setup_reddit()
    all_usernames = get_all_moderator_usernames()
    
    # Get user inputs
    max_mods = len(all_usernames)
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
    
    selected = all_usernames[:mod_count]
    
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