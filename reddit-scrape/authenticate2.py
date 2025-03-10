import tkinter as tk
from tkinter import messagebox, ttk
import threading
import json
import time
from datetime import datetime
import requests
from base64 import b64encode

# Reddit API Configuration
REDDIT_CLIENT_ID = 'dJ3T_uEzjVDzDor7AYhjQw'
REDDIT_CLIENT_SECRET = '9jqS61XscMGA3OC5VHEEd7RicqLO5g'
REDDIT_USERNAME = 'khanrazawaseem'
REDDIT_PASSWORD = 'fb3bbc2c'
USER_AGENT = 'python:post-collector:v1.0 (by /u/khanrazawaseem)'

# GitHub Configuration
GITHUB_TOKEN = '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'
GITHUB_OWNER = 'wk23aau'
GITHUB_REPO = 'distress-detector'
GITHUB_BRANCH = 'main'
GITHUB_PATH = 'data/raw/reddit-posts/'

class RedditScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit Data Scraper")
        self.root.geometry("600x400")

        # UI Components
        self.subreddit_label = ttk.Label(root, text="Subreddit:")
        self.subreddit_entry = ttk.Entry(root, width=30)
        self.subreddit_entry.insert(0, "TrueOffMyChest")

        self.posts_label = ttk.Label(root, text="Total Posts:")
        self.posts_entry = ttk.Entry(root, width=10)
        self.posts_entry.insert(0, "100")

        self.batch_label = ttk.Label(root, text="Batch Size:")
        self.batch_entry = ttk.Entry(root, width=10)
        self.batch_entry.insert(0, "50")

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.log_text = tk.Text(root, height=10, width=60)
        self.start_button = ttk.Button(root, text="Start Scraping", command=self.start_scraping)

        # Layout
        self.subreddit_label.grid(row=0, column=0, padx=5, pady=5)
        self.subreddit_entry.grid(row=0, column=1, padx=5, pady=5)
        self.posts_label.grid(row=1, column=0, padx=5, pady=5)
        self.posts_entry.grid(row=1, column=1, padx=5, pady=5)
        self.batch_label.grid(row=2, column=0, padx=5, pady=5)
        self.batch_entry.grid(row=2, column=1, padx=5, pady=5)
        self.start_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.progress.grid(row=4, column=0, columnspan=2, padx=20)
        self.log_text.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def get_reddit_token(self):
        try:
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
        except Exception as e:
            self.log(f"Authentication Error: {str(e)}")
            return None

    def fetch_batch(self, subreddit, batch_size, after=None):
        token = self.get_reddit_token()
        if not token:
            return [], None

        headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': USER_AGENT
        }
        params = {
            'limit': min(batch_size, 100),
            'after': after
        }

        try:
            response = requests.get(f'https://oauth.reddit.com/r/{subreddit}/new',
                                    headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data['data']['children'], data['data']['after']
        except Exception as e:
            self.log(f"Fetch Error: {str(e)}")
            return [], None

    def clean_data(self, posts):
        essential_fields = {
            'id', 'title', 'selftext', 'subreddit', 'created_utc',
            'num_comments', 'score', 'upvote_ratio', 'author_flair_text',
            'link_flair_text', 'url', 'url_overridden_by_dest',
            'preview', 'media', 'secure_media'
        }

        cleaned = []
        for post in posts:
            data = post['data']
            cleaned_post = {k: v for k, v in data.items() if k in essential_fields}
            
            if 'created_utc' in cleaned_post:
                utc_time = datetime.utcfromtimestamp(cleaned_post['created_utc'])
                cleaned_post['created_utc'] = utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            cleaned.append(cleaned_post)
        return cleaned

    def upload_to_github(self, filename, content):
        url = f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}{filename}'
        formatted = json.dumps(content, indent=2)
        encoded = b64encode(formatted.encode()).decode()

        payload = {
            'message': f'UI Upload: {filename}',
            'content': encoded,
            'branch': GITHUB_BRANCH
        }

        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.put(url, data=json.dumps(payload), headers=headers)
            response.raise_for_status()
            self.log(f"Uploaded: {filename}")
        except Exception as e:
            self.log(f"Upload Error: {str(e)}")

    def scrape(self):
        subreddit = self.subreddit_entry.get().strip()
        total_posts = int(self.posts_entry.get())
        batch_size = int(self.batch_entry.get())
        
        self.log(f"Starting scrape: r/{subreddit} ({total_posts} posts, {batch_size} batch size)")
        self.progress['maximum'] = total_posts
        collected = 0
        after = None

        while collected < total_posts:
            current_batch = min(batch_size, total_posts - collected)
            self.log(f"Fetching batch of {current_batch} posts...")
            
            batch, after = self.fetch_batch(subreddit, current_batch, after)
            if not batch:
                self.log("No more posts available")
                break

            cleaned = self.clean_data(batch)
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'{subreddit}_{collected+1}-{collected+len(cleaned)}_{timestamp}.json'
            
            self.upload_to_github(filename, cleaned)
            collected += len(cleaned)
            
            self.progress['value'] = collected
            self.log(f"Progress: {collected}/{total_posts}")
            time.sleep(2)

        self.log("Scraping completed!")

    def start_scraping(self):
        try:
            # Validate inputs
            int(self.posts_entry.get())
            int(self.batch_entry.get())
            
            # Disable button during operation
            self.start_button.config(state=tk.DISABLED)
            
            # Run in separate thread
            threading.Thread(target=self.scrape).start()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for posts and batch size")
        except Exception as e:
            self.log(f"Unexpected Error: {str(e)}")
            self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = RedditScraperApp(root)
    root.mainloop()