import os
import praw
import pandas as pd
import yaml
import sqlite3
import json
from tqdm import tqdm
import time
import re
import prawcore  # To handle rate limit exceptions

# Load configuration from YAML (e.g., config/config.yaml)
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

def load_subreddits(file_path):
    """
    Loads a list of subreddits from a JSON or CSV file.
    If JSON, expects a list of subreddit names.
    If CSV, expects a column named 'subreddit'.
    """
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            subreddits = json.load(f)
        return subreddits  # e.g., ["depression", "anxiety", ...]
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        return df['subreddit'].tolist()
    else:
        raise ValueError("Unsupported file format for subreddits list.")

def create_db_and_tables(db_path):
    """
    Connects to a SQLite database and creates the posts table if it doesn't exist.
    The base table has 18 columns (excluding the auto-increment id).
    New columns (for flair and comments) will be added with ALTER TABLE.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,
            subreddit TEXT,
            title TEXT,
            selftext TEXT,
            created_utc REAL,
            score INTEGER,
            upvote_ratio REAL,
            ups INTEGER,
            downs INTEGER,
            num_comments INTEGER,
            url TEXT,
            permalink TEXT,
            is_self INTEGER,
            media_urls TEXT,
            user_name TEXT,
            user_link_karma INTEGER,
            user_comment_karma INTEGER,
            user_created_utc REAL
        )
    ''')
    conn.commit()
    return conn

def update_table_schema(conn):
    """
    Alters the posts table to add new columns if they don't exist.
    New columns: link_flair_text, author_flair_text, comments.
    Total columns after update will be 21 (excluding the id).
    """
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE posts ADD COLUMN link_flair_text TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print(e)
    try:
        c.execute("ALTER TABLE posts ADD COLUMN author_flair_text TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print(e)
    try:
        c.execute("ALTER TABLE posts ADD COLUMN comments TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            print(e)
    conn.commit()

def clean_text(text):
    """
    Cleans text by removing URLs, mentions, hashtags, and extra whitespace.
    Optionally lowercases text based on configuration.
    """
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    if config['preprocessing']['text']['do_lower_case']:
        text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def scrape_post(submission, reddit, max_retries=5):
    """
    Scrapes details from a single submission, including:
      - Post metadata (title, selftext, created time, voting info)
      - Media URLs (if available)
      - User metadata (username, karma, account creation)
      - Flair content (link and author flair)
      - All comments (as a JSON string)
    Uses exponential backoff for rate limiting.
    """
    retry_delay = 5
    retries = 0

    while retries < max_retries:
        try:
            # Basic post details
            post_data = {
                "post_id": submission.id,
                "subreddit": submission.subreddit.display_name,
                "title": clean_text(submission.title),
                "selftext": clean_text(submission.selftext),
                "created_utc": submission.created_utc,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "ups": getattr(submission, "ups", None),
                "downs": getattr(submission, "downs", None),
                "num_comments": submission.num_comments,
                "url": submission.url,
                "permalink": submission.permalink,
                "is_self": int(submission.is_self)
            }
            # Retrieve flair content (using getattr to avoid missing attributes)
            post_data["link_flair_text"] = getattr(submission, "link_flair_text", None)
            post_data["author_flair_text"] = getattr(submission, "author_flair_text", None)

            # Media URLs: record if URL looks like image/video
            media_urls = []
            if submission.url and submission.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov')):
                media_urls.append(submission.url)
            if hasattr(submission, 'media') and submission.media:
                media_urls.append(json.dumps(submission.media))
            post_data["media_urls"] = json.dumps(media_urls) if media_urls else None

            # User metadata
            user = submission.author
            if user:
                try:
                    post_data["user_name"] = str(user)
                    post_data["user_link_karma"] = user.link_karma
                    post_data["user_comment_karma"] = user.comment_karma
                    post_data["user_created_utc"] = user.created_utc
                except Exception as e:
                    post_data["user_name"] = str(user)
                    post_data["user_link_karma"] = None
                    post_data["user_comment_karma"] = None
                    post_data["user_created_utc"] = None
            else:
                post_data["user_name"] = None
                post_data["user_link_karma"] = None
                post_data["user_comment_karma"] = None
                post_data["user_created_utc"] = None

            # Retrieve all comments as a list
            submission.comments.replace_more(limit=None)
            comments_list = []
            for comment in submission.comments.list():
                comment_data = {
                    "comment_id": comment.id,
                    "user": str(comment.author) if comment.author else None,
                    "comment_text": clean_text(comment.body),
                    "created_utc": comment.created_utc,
                    "score": comment.score,
                    "permalink": comment.permalink
                }
                comments_list.append(comment_data)
            post_data["comments"] = json.dumps(comments_list) if comments_list else None

            return post_data

        except prawcore.exceptions.TooManyRequests as e:
            print(f"Rate limit encountered: {e}. Sleeping for {retry_delay} seconds.")
            time.sleep(retry_delay)
            retries += 1
            retry_delay *= 2
        except Exception as e:
            print(f"Error scraping post {submission.id}: {e}")
            return None

    print(f"Max retries reached for post {submission.id}. Skipping.")
    return None

def save_post_to_db(conn, post):
    """
    Inserts a single scraped post (with its comments) into the SQLite database.
    Uses INSERT OR IGNORE to skip posts whose post_ids already exist.
    Commits immediately after the insert.
    """
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO posts (
                post_id, subreddit, title, selftext, created_utc, score, upvote_ratio, ups, downs, num_comments,
                url, permalink, is_self, media_urls, user_name, user_link_karma, user_comment_karma, user_created_utc,
                link_flair_text, author_flair_text, comments
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            post.get("post_id"),
            post.get("subreddit"),
            post.get("title"),
            post.get("selftext"),
            post.get("created_utc"),
            post.get("score"),
            post.get("upvote_ratio"),
            post.get("ups"),
            post.get("downs"),
            post.get("num_comments"),
            post.get("url"),
            post.get("permalink"),
            post.get("is_self"),
            post.get("media_urls"),
            post.get("user_name"),
            post.get("user_link_karma"),
            post.get("user_comment_karma"),
            post.get("user_created_utc"),
            post.get("link_flair_text"),
            post.get("author_flair_text"),
            post.get("comments")
        ))
        conn.commit()
    except Exception as e:
        print(f"Error inserting post {post.get('post_id')} into DB: {e}")

def scrape_and_save_subreddit(reddit, conn, subreddit_name, limit=100):
    """
    Scrapes posts from a subreddit and writes each post (with its comments) to the DB immediately.
    Handles exceptions (like NotFound) so that the process continues with other subreddits.
    """
    try:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scraping posts from r/{subreddit_name} ...")
        for submission in tqdm(subreddit.top(limit=limit), desc=f"r/{subreddit_name} posts", unit="post"):
            post_data = scrape_post(submission, reddit)
            if post_data:
                save_post_to_db(conn, post_data)
    except prawcore.exceptions.NotFound as e:
        print(f"Subreddit r/{subreddit_name} not found or inaccessible: {e}. Skipping.")
    except Exception as e:
        print(f"Error processing subreddit r/{subreddit_name}: {e}")

def main():
    # Load subreddits from file (JSON or CSV)
    subreddits_file = config.get("reddit", {}).get("subreddits_file", "subreddits.json")
    subreddits_list = load_subreddits(subreddits_file)

    # Connect to SQLite database and update schema
    db_path = config.get("data", {}).get("db_path", "reddit_data.db")
    conn = create_db_and_tables(db_path)
    update_table_schema(conn)

    # Initialize Reddit API using credentials from environment variables
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )

    # For each subreddit, scrape posts and immediately write each post to the DB.
    for subreddit in subreddits_list:
        scrape_and_save_subreddit(
            reddit, conn, subreddit,
            limit=config.get("reddit", {}).get("data_collection_limit", 100)
        )
        time.sleep(1)  # Avoid hitting API rate limits

    conn.close()
    print("Scraping complete. Data stored in SQLite database.")

if __name__ == "__main__":
    main()
