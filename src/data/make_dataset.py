import os
import praw
import pandas as pd
import yaml
from tqdm import tqdm
import time
import requests
from io import BytesIO
import re

# Load configuration
with open("experiments/config.yaml", "r") as f:
    config = yaml.safe_load(f)

def get_seed_users(subreddits, limit_per_subreddit=100):
    """Gets seed users, with a progress bar for each subreddit."""
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )

    seed_users = set()
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        try:
            with tqdm(total=limit_per_subreddit, desc=f"Getting seed users from r/{subreddit_name}", unit="user") as pbar:
                for submission in subreddit.top(limit=limit_per_subreddit):
                    if submission.author:
                        seed_users.add(str(submission.author))
                        pbar.update(1)  # Update for each user found
        except Exception as e:
            print(f"Error getting users from {subreddit_name}: {e}")
    return seed_users

def get_user_data(username, reddit, pbar):
    """Retrieves user posts/comments, updating a given progress bar."""
    try:
        user = reddit.redditor(username)
        user_posts = []
        for submission in user.submissions.new(limit=None):
            post_data = {
                "post_id": submission.id,
                "user": username,
                "subreddit": submission.subreddit.display_name,
                "title": submission.title,
                "selftext": submission.selftext,
                "created_utc": submission.created_utc,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "upvote_ratio": submission.upvote_ratio,
                "url": submission.url,
                "permalink": submission.permalink,
                "is_self": submission.is_self,
                "image_url": submission.url if submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')) else None,
            }
            user_posts.append(post_data)
            pbar.update(1)  # Update for each post
        user_posts_df = pd.DataFrame(user_posts)

        user_comments = []
        for comment in user.comments.new(limit=None):
            comment_data = {
                "comment_id": comment.id,
                "user": username,
                "subreddit": comment.subreddit.display_name,
                "comment_text": comment.body,
                "created_utc": comment.created_utc,
                "score": comment.score,
                "parent_post_id": comment.submission.id,
                "permalink": comment.permalink,
            }
            user_comments.append(comment_data)
            pbar.update(1)  # Update for each comment
        user_comments_df = pd.DataFrame(user_comments)

        return user_posts_df, user_comments_df

    except Exception as e:
        print(f"Error retrieving data for user {username}: {e}")
        return None, None

def get_post_data(post_id, reddit, pbar_context):
    """Retrieves context post data, updating a given progress bar."""
    try:
        submission = reddit.submission(id=post_id)
        post_data = {
            "post_id": submission.id,
            "user": str(submission.author),
            "subreddit": submission.subreddit.display_name,
            "title": submission.title,
            "selftext": submission.selftext,
            "created_utc": submission.created_utc,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "upvote_ratio": submission.upvote_ratio,
            "url": submission.url,
            "permalink": submission.permalink,
            "is_self": submission.is_self,
            "image_url": submission.url if submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')) else None,
        }
        pbar_context.update(1)  # Update for each context post
        return post_data
    except Exception as e:
        print(f"Error retrieving post data for ID {post_id}: {e}")
        return None

def get_comments_for_post(post_id, reddit, pbar_comments):
    """Retrieves comments for a post, updating a progress bar."""
    try:
        submission = reddit.submission(id=post_id)
        comments = []
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            comment_data = {
                "comment_id": comment.id,
                "user": str(comment.author),
                "subreddit": comment.subreddit.display_name,
                "comment_text": comment.body,
                "created_utc": comment.created_utc,
                "score": comment.score,
                "parent_post_id": comment.submission.id,  # Redundant, but consistent
                "permalink": comment.permalink,
            }
            comments.append(comment_data)
            pbar_comments.update(1) # Update per comment.
        return pd.DataFrame(comments)

    except Exception as e:
        print(f"Error retrieving comments for post {post_id}: {e}")
        return None

def download_images(df, image_dir, id_column, pbar):
    """Downloads images, updating a given progress bar."""
    if 'image_url' not in df.columns or df['image_url'].isnull().all():
        print("No image URLs to download.")
        return df

    os.makedirs(image_dir, exist_ok=True)
    image_paths = []

    for _, row in df.iterrows():
        image_url = row['image_url']
        if pd.notna(image_url):
            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()

                content_type = response.headers.get('content-type')
                ext = '.' + content_type.split('/')[-1] if 'image' in content_type else None
                if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    ext = '.jpg'

                if ext:
                    image_path = os.path.join(image_dir, str(row[id_column]) + ext)
                    with open(image_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    image_paths.append(image_path)
                else:
                    image_paths.append(None)
            except Exception as e:
                print(f"Error downloading/saving image from {image_url}: {e}")
                image_paths.append(None)
        else:
            image_paths.append(None)
        pbar.update(1)  # Update for each image (attempted download)
    df['image_path'] = image_paths
    return df

def clean_text(text):
    """Basic text cleaning function."""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    if config['preprocessing']['text']['do_lower_case']:
        text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_data(df, text_columns):
    """Preprocesses a dataframe."""
    if df is None or df.empty:
        return df
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna("").apply(clean_text)
    return df

def save_data(df, file_path):
    """Saves the DataFrame, creating directories if needed."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False)
        print(f"Data saved to: {file_path}")
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")


def main():
    # --- 1. Get Seed Users ---
    print("Getting seed users...")
    seed_users = get_seed_users(
        config["reddit"]["subreddits"],
        limit_per_subreddit=config["reddit"]["data_collection_limit"]
    )
    print(f"Found {len(seed_users)} seed users.")

    # --- 2. Collect Data for Each User ---
    all_user_posts = []
    all_user_comments = []
    all_context_posts = []
    processed_post_ids = set()

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )
    # Outer progress bar for users
    with tqdm(total=len(seed_users), desc="Collecting User Data", unit="user") as pbar_users:
        for username in seed_users:
            # Inner progress bar for posts/comments within each user
            with tqdm(desc=f"  Posts/Comments for {username}", unit="item") as pbar_user_items:
                user_posts_df, user_comments_df = get_user_data(username, reddit, pbar_user_items)

            if user_posts_df is not None:
                all_user_posts.append(user_posts_df)
            if user_comments_df is not None:
                all_user_comments.append(user_comments_df)

                # Progress bar for context posts
                with tqdm(total=len(user_comments_df['parent_post_id'].unique()), desc=f"    Context Posts for {username}'s comments", unit="post") as pbar_context:
                    for post_id in user_comments_df['parent_post_id'].unique():
                        if post_id not in processed_post_ids:
                            context_post = get_post_data(post_id, reddit, pbar_context)
                            if context_post:
                                all_context_posts.append(context_post)
                                processed_post_ids.add(post_id)

            # Get comments of the posts of the current user.
            if user_posts_df is not None:
                with tqdm(total=len(user_posts_df), desc=f"    Comments for posts of {username}", unit="post") as pbar_comments:
                    for post_id in user_posts_df['post_id']:
                        comments_df = get_comments_for_post(post_id, reddit, pbar_comments)
                        if comments_df is not None:
                            all_user_comments.append(comments_df)  #Consistent data

            pbar_users.update(1)  # Update outer progress bar (users)
            time.sleep(1)

    # --- 3. Combine DataFrames ---
    if all_user_posts:
        all_user_posts_df = pd.concat(all_user_posts, ignore_index=True)
    else:
        all_user_posts_df = pd.DataFrame()

    if all_user_comments:
        all_user_comments_df = pd.concat(all_user_comments, ignore_index=True)
    else:
        all_user_comments_df = pd.DataFrame()

    if all_context_posts:
        all_context_posts_df = pd.DataFrame(all_context_posts)
    else:
        all_context_posts_df = pd.DataFrame()

    # --- 4. Download Images ---
    print("Downloading images...")
    with tqdm(total=len(all_user_posts_df) + len(all_context_posts_df), desc="Downloading All Images", unit="image") as pbar_images:
        if not all_user_posts_df.empty:
            all_user_posts_df = download_images(all_user_posts_df, os.path.join(config["data"]["raw_data_dir"], "user_posts_images"), "post_id", pbar_images)
        if not all_context_posts_df.empty:
            all_context_posts_df = download_images(all_context_posts_df, os.path.join(config["data"]["raw_data_dir"], "context_posts_images"), "post_id", pbar_images)

    # --- 5. Preprocess Data ---
    all_user_posts_df = preprocess_data(all_user_posts_df, ['title', 'selftext'])
    all_user_comments_df = preprocess_data(all_user_comments_df, ['comment_text'])
    all_context_posts_df = preprocess_data(all_context_posts_df, ['title', 'selftext'])

    # --- 6. Save Data ---
    print("Saving data...")
    if not all_user_posts_df.empty:
        save_data(all_user_posts_df, os.path.join(config["data"]["raw_data_dir"], "user_posts.csv"))
    if not all_user_comments_df.empty:
        save_data(all_user_comments_df, os.path.join(config["data"]["raw_data_dir"], "user_comments.csv"))
    if not all_context_posts_df.empty:
        save_data(all_context_posts_df, os.path.join(config["data"]["raw_data_dir"], "context_posts.csv"))

    print("Data collection and preprocessing complete.")

if __name__ == "__main__":
    main()