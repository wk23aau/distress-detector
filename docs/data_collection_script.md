# Reddit Moderator Activity Grabber

A comprehensive tool to collect and analyze Reddit moderator activity, including:
- Moderator's own posts and comments
- Comments by other users on moderator's posts
- Activity summaries and progress tracking

## Features
✅ **Full Data Collection**  
   - Collects posts, comments, and nested comments
   - Handles private accounts and rate limits gracefully

✅ **Progress Tracking**  
   - Multi-level progress bars for posts, comments, and nested comments
   - Real-time activity summary display

✅ **Flexible Limits**  
   - Set custom collection limits or collect all available data
   - Automatic detection of total available activity

✅ **Structured Output**  
   - Timestamped JSON and CSV files
   - Separate directories per moderator

## Prerequisites
- Python 3.8+
- Reddit API credentials (client ID/secret)
- Required packages: `praw`, `tqdm`, `python-dotenv`

## Installation
1. Clone this repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
   
**Command-line prompts** :

1.  Select number of moderators to process
    
2.  Set post collection limit (blank = collect all)
    
3.  Set comment collection limit (blank = collect all)

```bash
data/raw/moderator-posts/
├── AutoModerator/
│   ├── posts_with_comments_1500_20231010.json
│   ├── posts_1500_20231010.csv
│   ├── moderator_comments_2500_20231010.csv
│   └── moderator_comments_2500_20231010.json
└── spez/
    └── ...
```
## Key Metrics Tracked
-------------------

**Data Type** Moderator Posts, Moderator Comments, Nested Comments and Activity Summary

***Description** Original posts created by moderators, Comments made by moderators anywhere, Comments by others on moderator's posts and Total posts/comments per moderator

Notes
-----

⚠️ **Rate Limits**

*   Built-in 5-second delay between moderators
    
*   Automatic 60-second pause on rate limit errors
    

🔒 **Data Privacy**

*   Does NOT collect:
    
    *   Private messages
        
    *   Deleted content
        
    *   Personal information beyond public Reddit activity