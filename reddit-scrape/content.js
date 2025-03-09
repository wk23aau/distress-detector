(function() {
    // Unicode-safe Base64 encoding function.
    function base64EncodeUnicode(str) {
      return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, 
        function(match, p1) {
          return String.fromCharCode(parseInt(p1, 16));
        }
      ));
    }
  
    // Helper: wait for a specified number of milliseconds.
    const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  
    // Returns a human-readable timestamp in the format YYYY-MM-DD_HH-mm-ss.
    function getHumanReadableTimestamp() {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hour = String(now.getHours()).padStart(2, '0');
      const minute = String(now.getMinutes()).padStart(2, '0');
      const second = String(now.getSeconds()).padStart(2, '0');
      return `${year}-${month}-${day}_${hour}-${minute}-${second}`;
    }
  
    // Global maps/arrays for collected posts.
    const collectedPosts = new Map(); // To avoid duplicates across batches.
    let currentBatch = []; // Stores posts for current batch.
    let cumulativeCount = 0; // Total posts collected (unique).
  
    // Extract data from a <shreddit-post> element.
    const extractPostData = (post) => {
      const postId = post.getAttribute('id');
      if (!postId || collectedPosts.has(postId)) return; // Skip duplicates
  
      const shadow = post.shadowRoot;
      if (!shadow) return;
  
      // Extract title from an <a> element with slot="title" (light DOM).
      const titleElement = post.querySelector('a[slot="title"]');
      const title = titleElement ? titleElement.textContent.trim() : "Not found";
  
      // Extract post content (paragraphs) from the element with slot="text-body".
      let content = "";
      const contentElement = post.querySelector('a[slot="text-body"] div.md');
      if (contentElement) {
        content = Array.from(contentElement.querySelectorAll('p'))
                  .map(p => p.textContent.trim())
                  .join('\n\n');
      } else {
        content = "Not found";
      }
  
      // Extract vote count (score) from the shadow DOM.
      const scoreElement = shadow.querySelector('[data-post-click-location="vote"] faceplate-number[pretty]');
      const score = scoreElement 
        ? (scoreElement.getAttribute('number') || scoreElement.textContent.trim())
        : 'Not found';
  
      // Extract comments count from the shadow DOM.
      const commentElement = shadow.querySelector('[data-post-click-location="comments-button"] faceplate-number');
      const comments = commentElement 
        ? (commentElement.getAttribute('number') || commentElement.textContent.trim())
        : 'Not found';
  
      const postData = { postId, title, content, score, comments };
      collectedPosts.set(postId, postData);
      currentBatch.push(postData);
      console.log(`Collected post: ${title.slice(0, 30)}...`);
    };
  
    // Generate CSV from an array of post objects.
    function generateCSVFromArray(postsArray) {
      let csv = "Post ID,Title,Content,Votes,Comments\n";
      postsArray.forEach(post => {
        csv += `"${post.postId.replace(/"/g, '""')}","${post.title.replace(/"/g, '""')}","${post.content.replace(/"/g, '""')}","${post.score}","${post.comments}"\n`;
      });
      return csv;
    }
  
    // Generate JSON string from an array of post objects.
    function getJSONData(postsArray) {
      return JSON.stringify(postsArray, null, 2);
    }
  
    // Upload a file to GitHub via the API.
    function uploadFileToGitHub(fileName, content, token) {
      const owner = "wk23aau";
      const repo = "distress-detector";
      const path = "data/raw/reddit-posts/" + fileName;
      const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
      const encodedContent = base64EncodeUnicode(content);
      const body = JSON.stringify({
        message: "Auto-uploaded reddit posts via scraper",
        content: encodedContent,
        branch: "main"
      });
      console.log(`Uploading ${fileName} to GitHub...`);
      return fetch(apiUrl, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "token " + token
        },
        body: body
      }).then(response => response.json());
    }
  
    // Extract subreddit name from the URL.
    function getSubredditName() {
      const parts = window.location.pathname.split("/");
      return parts.length >= 3 ? parts[2] : "UnknownSubreddit";
    }
  
    // Automatically upload the current batch as CSV and JSON files.
    async function autoUploadBatch(batchPosts) {
      const token = "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";
      const subreddit = getSubredditName();
      const timestamp = getHumanReadableTimestamp();
      const count = batchPosts.length;
      const csvFileName = `${subreddit}_${timestamp}_${count}.csv`;
      const jsonFileName = `${subreddit}_${timestamp}_${count}.json`;
      console.log(`Uploading batch of ${count} posts as ${csvFileName} and ${jsonFileName}`);
      const csvData = generateCSVFromArray(batchPosts);
      const jsonData = getJSONData(batchPosts);
      await uploadFileToGitHub(csvFileName, csvData, token);
      await uploadFileToGitHub(jsonFileName, jsonData, token);
    }
  
    // Main batched collection function.
    async function collectPostsBatched() {
      // Prompt for total collection parameters.
      const totalTimeInput = window.prompt("Enter total collection time (minutes):", "5");
      const totalPostsInput = window.prompt("Enter target total number of posts:", "1000");
      const batchTimeInput = window.prompt("Enter batch time (minutes):", "1");
      const batchSizeInput = window.prompt("Enter batch size (posts):", "100");
  
      let totalTimeMs = parseFloat(totalTimeInput) * 60000;
      let targetTotalPosts = parseInt(totalPostsInput, 10);
      let batchTimeMs = parseFloat(batchTimeInput) * 60000;
      let batchSize = parseInt(batchSizeInput, 10);
      if (isNaN(totalTimeMs) || totalTimeMs <= 0) totalTimeMs = 5 * 60000;
      if (isNaN(targetTotalPosts) || targetTotalPosts <= 0) targetTotalPosts = 1000;
      if (isNaN(batchTimeMs) || batchTimeMs <= 0) batchTimeMs = 1 * 60000;
      if (isNaN(batchSize) || batchSize <= 0) batchSize = 100;
  
      const overallStartTime = Date.now();
      let batchStartTime = Date.now();
  
      while(cumulativeCount < targetTotalPosts && (Date.now() - overallStartTime) < totalTimeMs) {
        window.scrollBy(0, 2000);
        await wait(1000);
        document.querySelectorAll('shreddit-post').forEach(post => extractPostData(post));
  
        // If batch condition is met, upload the batch.
        if ((Date.now() - batchStartTime) >= batchTimeMs || currentBatch.length >= batchSize) {
          console.log(`Batch condition met: uploading batch of ${currentBatch.length} posts.`);
          await autoUploadBatch(currentBatch);
          cumulativeCount += currentBatch.length;
          currentBatch = [];
          batchStartTime = Date.now();
        }
      }
      // Upload any remaining posts.
      if (currentBatch.length > 0) {
        console.log(`Final batch: uploading remaining ${currentBatch.length} posts.`);
        await autoUploadBatch(currentBatch);
        cumulativeCount += currentBatch.length;
        currentBatch = [];
      }
      console.log(`Finished: Total collected posts: ${cumulativeCount}`);
      displayCollectedPosts(Array.from(collectedPosts.values()));
    }
  
    // Display collected posts in a modal overlay with download options.
    function displayCollectedPosts(posts) {
      const existingContainer = document.getElementById("redditPostsContainer");
      if (existingContainer) existingContainer.remove();
  
      const container = document.createElement("div");
      container.id = "redditPostsContainer";
      Object.assign(container.style, {
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        backgroundColor: "#fff",
        padding: "20px",
        border: "1px solid #ccc",
        borderRadius: "8px",
        maxHeight: "80vh",
        overflowY: "auto",
        zIndex: "10000",
        width: "80%",
        maxWidth: "600px",
        fontFamily: "Arial, sans-serif"
      });
  
      let html = `<h2>Collected Posts (${posts.length})</h2>`;
      posts.forEach(post => {
        html += `<div style="margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee;">
          <p><strong>Post ID:</strong> ${post.postId}</p>
          <p><strong>Title:</strong> ${post.title}</p>
          <p><strong>Content:</strong> ${post.content}</p>
          <p><strong>Votes:</strong> ${post.score} &nbsp; <strong>Comments:</strong> ${post.comments}</p>
        </div>`;
      });
      html += `<div style="text-align: right;">
        <button id="downloadCSV" style="padding: 8px 12px; margin-right: 10px;">Download CSV</button>
        <button id="downloadJSON" style="padding: 8px 12px; margin-right: 10px;">Download JSON</button>
        <button id="closeRedditPosts" style="padding: 8px 12px;">Close</button>
      </div>`;
      container.innerHTML = html;
      document.body.appendChild(container);
  
      document.getElementById("closeRedditPosts").onclick = () => container.remove();
      document.getElementById("downloadCSV").onclick = () => {
        const csvData = generateCSVFromArray(posts);
        const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "reddit_posts.csv";
        document.body.appendChild(link);
        link.click();
        link.remove();
      };
      document.getElementById("downloadJSON").onclick = () => {
        const jsonData = getJSONData(posts);
        const blob = new Blob([jsonData], { type: "application/json;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "reddit_posts.json";
        document.body.appendChild(link);
        link.click();
        link.remove();
      };
    }
  
    // Add a floating button to trigger the batched post collection process.
    function addCollectButton() {
      const btnContainer = document.createElement("div");
      Object.assign(btnContainer.style, {
        position: "fixed",
        top: "10px",
        right: "10px",
        zIndex: "10000"
      });
      const button = document.createElement("button");
      button.innerText = "Collect Posts";
      Object.assign(button.style, {
        padding: "10px 15px",
        backgroundColor: "#007bff",
        color: "#fff",
        border: "none",
        borderRadius: "5px",
        cursor: "pointer",
        fontFamily: "Arial, sans-serif"
      });
      button.onclick = collectPostsBatched;
      btnContainer.appendChild(button);
      document.body.appendChild(btnContainer);
    }
  
    // Initialize the script when the page loads.
    window.addEventListener("load", addCollectButton);
  })();
  