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
  
    // Return a human-readable timestamp in the format YYYY-MM-DD_HH-mm-ss.
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
  
    // Global storage.
    const collectedPosts = new Map(); // All unique posts across batches.
    let currentBatch = [];            // Posts in current batch.
    let cumulativeCount = 0;          // Total posts collected.
  
    // Extract data from a <shreddit-post> element.
    const extractPostData = (post) => {
      const postId = post.getAttribute('id');
      if (!postId || collectedPosts.has(postId)) return; // Skip duplicates
  
      const shadow = post.shadowRoot;
      if (!shadow) return;
  
      // Extract title from an <a> element with slot="title" (light DOM).
      const titleElement = post.querySelector('a[slot="title"]');
      const title = titleElement ? titleElement.textContent.trim() : "Not found";
  
      // Extract content (paragraphs) from element with slot="text-body".
      let content = "";
      const contentElement = post.querySelector('a[slot="text-body"] div.md');
      if (contentElement) {
        content = Array.from(contentElement.querySelectorAll('p'))
                  .map(p => p.textContent.trim())
                  .join('\n\n');
      } else {
        content = "Not found";
      }
  
      // Extract vote count (score) from shadow DOM.
      const scoreElement = shadow.querySelector('[data-post-click-location="vote"] faceplate-number[pretty]');
      const score = scoreElement 
        ? (scoreElement.getAttribute('number') || scoreElement.textContent.trim())
        : 'Not found';
  
      // Extract comments count from shadow DOM.
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
  
    // Extract subreddit name from URL.
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
  
        // If batch time or batch size condition met, upload current batch.
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
  
    // Enhanced UI Initialization inspired by Amazon script.
    function addStylishCollectButton() {
      const container = document.createElement("div");
      Object.assign(container.style, {
        position: "fixed",
        top: "15px",
        right: "15px",
        zIndex: "99999",
        display: "flex",
        flexDirection: "column",
        gap: "10px"
      });
  
      const collectBtn = document.createElement("button");
      collectBtn.textContent = "🚀 Collect Reddit Posts";
      Object.assign(collectBtn.style, {
        padding: "10px 15px",
        backgroundColor: "#007bff",
        color: "#fff",
        borderRadius: "5px",
        border: "none",
        cursor: "pointer",
        fontSize: "15px",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
        transition: "transform 0.2s, background-color 0.3s"
      });
  
      collectBtn.onmouseover = () => collectBtn.style.backgroundColor = "#0056b3";
      collectBtn.onmouseout = () => collectBtn.style.backgroundColor = "#007bff";
      collectBtn.onmousedown = () => collectBtn.style.transform = "scale(0.96)";
      collectBtn.onmouseup = () => collectBtn.style.transform = "scale(1)";
  
      collectBtn.onclick = collectPostsBatched;
  
      container.appendChild(collectBtn);
      document.body.appendChild(container);
    }
  
    // Enhanced Modal UI for Displaying Collected Posts.
    function displayCollectedPosts(posts) {
      const existing = document.getElementById("redditPostsContainer");
      if (existing) existing.remove();
  
      const overlay = document.createElement("div");
      Object.assign(overlay.style, {
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        backgroundColor: "rgba(0,0,0,0.6)",
        zIndex: "9999",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
      });
  
      const modal = document.createElement("div");
      Object.assign(modal.style, {
        backgroundColor: "#fff",
        borderRadius: "12px",
        width: "80%",
        maxWidth: "700px",
        maxHeight: "80vh",
        overflowY: "auto",
        padding: "20px",
        boxShadow: "0 6px 16px rgba(0,0,0,0.3)"
      });
  
      modal.innerHTML = `
        <h2 style="margin-top:0; color:#333;">✅ Collected ${posts.length} Posts</h2>
        ${posts.map(post => `
          <div style="padding-bottom:10px; margin-bottom:10px; border-bottom:1px solid #ddd;">
            <p><strong>🆔 ID:</strong> ${post.postId}</p>
            <p><strong>📌 Title:</strong> ${post.title}</p>
            <p><strong>📖 Content:</strong> ${post.content}</p>
            <p>👍 <strong>Votes:</strong> ${post.score} &nbsp;&nbsp; 💬 <strong>Comments:</strong> ${post.comments}</p>
          </div>`).join('')}
        <div style="text-align:right;">
          <button id="downloadCSV" style="margin-right:10px;padding:8px 16px;background:#28a745;color:#fff;border:none;border-radius:6px;cursor:pointer;">📥 CSV</button>
          <button id="downloadJSON" style="margin-right:10px;padding:8px 16px;background:#f39c12;color:#fff;border:none;border-radius:6px;cursor:pointer;">📥 JSON</button>
          <button id="closeModal" style="padding:8px 16px;background:#e74c3c;color:#fff;border:none;border-radius:6px;cursor:pointer;">✖ Close</button>
        </div>
      `;
  
      overlay.appendChild(modal);
      document.body.appendChild(overlay);
  
      document.getElementById("closeModal").onclick = () => overlay.remove();
      document.getElementById("downloadCSV").onclick = () => {
        const csvData = generateCSVFromArray(posts);
        const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `Collected_Posts_${getHumanReadableTimestamp()}.csv`;
        link.click();
      };
  
      document.getElementById("downloadJSON").onclick = () => {
        const jsonData = getJSONData(posts);
        const blob = new Blob([jsonData], { type: "application/json;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `Collected_Posts_${getHumanReadableTimestamp()}.json`;
        link.click();
      };
    }
  
    // Initialize the stylish collect button on page load.
    window.addEventListener("load", addStylishCollectButton);
  })();
  