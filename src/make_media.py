import os
import sqlite3
import json
import requests
import time

def create_media_folder(base_folder, post_id):
    """Creates (or reuses) a folder for a given post inside the base folder."""
    folder = os.path.join(base_folder, post_id)
    os.makedirs(folder, exist_ok=True)
    return folder

def download_media_file(url, folder, filename, max_retries=5):
    """
    Downloads the file at 'url' into 'folder' with the given 'filename'.
    Implements retry logic with exponential backoff for rate limiting errors.
    """
    retry_delay = 5  # initial delay in seconds
    attempts = 0
    headers = {'User-Agent': 'Mozilla/5.0'}  # mimic a browser
    while attempts < max_retries:
        try:
            response = requests.get(url, stream=True, timeout=10, headers=headers)
            if response.status_code == 429:
                print(f"429 received from {url}. Attempt {attempts+1}/{max_retries}. Sleeping for {retry_delay} seconds.")
                time.sleep(retry_delay)
                retry_delay *= 2
                attempts += 1
                continue
            response.raise_for_status()

            # Try to extract file extension from URL
            url_filename = url.split("/")[-1]
            ext = os.path.splitext(url_filename)[1]
            if not ext:
                # Fallback: determine extension from content type
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    ext = '.jpg'
                elif 'video' in content_type:
                    ext = '.mp4'
                else:
                    ext = ''
            
            file_path = os.path.join(folder, f"{filename}{ext}")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return file_path
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            attempts += 1
            time.sleep(retry_delay)
            retry_delay *= 2
    return None

def process_new_media(db_path, media_base_folder):
    """
    Reads the database for posts with non-null media_urls.
    For each post, if the corresponding folder doesn't exist,
    creates the folder and downloads all media files.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT post_id, media_urls FROM posts WHERE media_urls IS NOT NULL")
    posts = c.fetchall()
    conn.close()

    for post_id, media_urls in posts:
        post_folder = os.path.join(media_base_folder, post_id)
        # If folder already exists, assume media is already downloaded.
        if os.path.exists(post_folder):
            continue
        try:
            urls = json.loads(media_urls)
        except Exception as e:
            print(f"Error parsing media_urls for post {post_id}: {e}")
            continue

        if not urls:
            continue

        post_folder = create_media_folder(media_base_folder, post_id)
        for idx, media_item in enumerate(urls):
            # If media_item is a string that looks like a dict, try to parse it.
            if isinstance(media_item, str) and media_item.strip().startswith("{"):
                try:
                    media_item = json.loads(media_item)
                except Exception as e:
                    print(f"Error parsing media_item in post {post_id}: {e}")
            # If it's now a dict (e.g., reddit_video), extract fallback_url.
            if isinstance(media_item, dict):
                if "reddit_video" in media_item:
                    url_str = media_item["reddit_video"].get("fallback_url")
                    if not url_str:
                        print(f"No fallback_url for reddit_video in post {post_id}")
                        continue
                else:
                    print(f"Unknown media object in post {post_id}: {media_item}")
                    continue
            else:
                url_str = media_item

            filename = f"{post_id}_{idx}"
            download_media_file(url_str, post_folder, filename)

def main():
    db_path = "reddit_data.db"  # Adjust if your database is located elsewhere.
    media_base_folder = os.path.join("data", "raw", "media")
    os.makedirs(media_base_folder, exist_ok=True)
    
    while True:
        print("Checking for new media...")
        process_new_media(db_path, media_base_folder)
        print("Sleeping for 5 minutes...")
        time.sleep(300)  # Wait for 5 minutes before re-checking.

if __name__ == "__main__":
    main()
