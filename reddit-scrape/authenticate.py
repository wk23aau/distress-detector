import requests
import json
import time
from datetime import datetime
from base64 import b64encode
from dotenv import load_dotenv
import os


# Load environment variables from .env
load_dotenv()

# Configuration (replace hardcoded values)
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH')
GITHUB_PATH = os.getenv('GITHUB_PATH')
USER_AGENT = 'python:post-collector:v1.0 (by /u/khanrazawaseem)'

def get_reddit_token():
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {
        'grant_type': 'password',
        'username': REDDIT_USERNAME,
        'password': REDDIT_PASSWORD
    }
    headers = {'User-Agent': USER_AGENT}
    
    response = requests.post('https://www.reddit.com/api/v1/access_token',
                            auth=auth, data=data, headers=headers)
    response.raise_for_status()
    return response.json()['access_token']

def fetch_batch(subreddit, batch_size, after=None):
    token = get_reddit_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': USER_AGENT
    }
    params = {
        'limit': min(batch_size, 1000),  # Reddit API max is 100
        'after': after
    }
    
    response = requests.get(f'https://oauth.reddit.com/r/{subreddit}/new',
                            headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return data['data']['children'], data['data']['after']


def fetch_raw_reddit_posts(subreddit, limit=10000):
    token = get_reddit_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': USER_AGENT
    }
    params = {'limit': 1000}
    posts = []
    after = None
    
    while len(posts) < limit:
        params['after'] = after
        response = requests.get(f'https://oauth.reddit.com/r/{subreddit}/new',
                                headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        children = data['data']['children']
        posts.extend(children)
        after = data['data']['after']
        print(f'Collected {len(posts)} raw posts...')
        time.sleep(2)
    
    return posts[:limit]

def clean_reddit_data(posts):
    essential_fields = {
        'id', 'title', 'selftext', 'subreddit', 'created_utc',
        'num_comments', 'score', 'upvote_ratio', 'author_flair_text',
        'link_flair_text', 'url', 'url_overridden_by_dest',
        'preview', 'media', 'secure_media'
    }
    
    cleaned_posts = []
    for post in posts:
        data = post['data']
        cleaned = {k: v for k, v in data.items() if k in essential_fields}
        
        # Convert Unix timestamp to human-readable format
        if 'created_utc' in cleaned:
            utc_time = datetime.utcfromtimestamp(cleaned['created_utc'])
            cleaned['created_utc'] = utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # ... (existing media handling code remains the same)

        cleaned_posts.append(cleaned)
    return cleaned_posts

def upload_to_github(filename, content):
    url = f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}{filename}'
    
    formatted_content = json.dumps(content, indent=2, sort_keys=True)
    encoded_content = b64encode(formatted_content.encode()).decode()
    
    payload = {
        'message': f'Clean data upload: {filename}',
        'content': encoded_content,
        'branch': GITHUB_BRANCH
    }
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.put(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
    print(f'Successfully uploaded {filename} to GitHub')

def main():
    try:
        subreddit = input("Enter subreddit name (e.g., 'TrueOffMyChest'): ")
        total_posts = int(input("Enter total number of posts to collect: "))
        batch_size = int(input("Enter batch size (max 100): "))
        batch_size = min(batch_size, 1000)
        
        collected = 0
        after = None
        
        while collected < total_posts:
            current_batch_size = min(batch_size, total_posts - collected)
            print(f"\nFetching batch of {current_batch_size} posts...")
            
            batch, after = fetch_batch(
                subreddit=subreddit,  # Use user-provided subreddit
                batch_size=current_batch_size,
                after=after
            )
            
            if not batch:
                print("No more posts available")
                break
                
            cleaned_batch = clean_reddit_data(batch)
            current_count = len(cleaned_batch)
            
            # Generate filename with subreddit name
            start = collected + 1
            end = collected + current_count
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'{subreddit}_{start}-{end}_{timestamp}.json'
            
            upload_to_github(filename, cleaned_batch)
            collected += current_count
            
            print(f"Batch saved: {filename}")
            print(f"Progress: {collected}/{total_posts} posts collected")
            
            time.sleep(2)
            
    except Exception as e:
        print(f'Error: {str(e)}')
        raise
if __name__ == '__main__':
    main()