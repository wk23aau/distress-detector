(function() {
    // Helper function to wait for a specified number of milliseconds
    const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  
    // Map to store unique post data (keyed by post id)
    const collectedPosts = new Map();
  
    // Function to extract data from a <shreddit-post> element
    const extractPostData = (post) => {
      const postId = post.getAttribute('id');
      if (!postId || collectedPosts.has(postId)) return; // Skip if already collected
  
      // Use the shadow DOM for certain elements
      const shadow = post.shadowRoot;
      if (!shadow) return;
  
      // Extract title from an <a> element with slot="title" (in light DOM)
      const titleElement = post.querySelector('a[slot="title"]');
      const title = titleElement ? titleElement.textContent.trim() : "Not found";
  
      // Extract post content (paragraphs) from the element with slot="text-body"
      let content = "";
      const contentElement = post.querySelector('a[slot="text-body"] div.md');
      if (contentElement) {
        content = Array.from(contentElement.querySelectorAll('p'))
                    .map(p => p.textContent.trim())
                    .join('\n\n');
      } else {
        content = "Not found";
      }
  
      // Extract vote count (score) from the shadow DOM
      const scoreElement = shadow.querySelector('[data-post-click-location="vote"] faceplate-number[pretty]');
      const score = scoreElement 
        ? (scoreElement.getAttribute('number') || scoreElement.textContent.trim())
        : 'Not found';
  
      // Extract comments count from the shadow DOM
      const commentElement = shadow.querySelector('[data-post-click-location="comments-button"] faceplate-number');
      const comments = commentElement 
        ? (commentElement.getAttribute('number') || commentElement.textContent.trim())
        : 'Not found';
  
      collectedPosts.set(postId, { postId, title, content, score, comments });
      console.log(`Collected post: ${title.slice(0, 30)}...`);
    };
  
    // Auto-scroll and collect posts based on user-defined criteria
    async function collectPosts() {
      collectedPosts.clear();
  
      // Prompt user for maximum scroll time (in minutes) and target post count
      const scrollTimeInput = window.prompt("Enter maximum scroll time (in minutes):", "1");
      const targetCountInput = window.prompt("Enter target number of posts to collect:", "100");
      let maxScrollTime = parseFloat(scrollTimeInput) * 60000; // Convert minutes to milliseconds
      let targetPostCount = parseInt(targetCountInput, 10);
      if (isNaN(maxScrollTime) || maxScrollTime <= 0) { maxScrollTime = 60000; } // default 1 minute
      if (isNaN(targetPostCount) || targetPostCount <= 0) { targetPostCount = 100; } // default 100 posts
  
      const startTime = Date.now();
      let attempts = 0;
      // Loop until either the target post count is reached or the maximum scroll time elapses.
      while (collectedPosts.size < targetPostCount && (Date.now() - startTime) < maxScrollTime && attempts < 1000) {
        window.scrollBy(0, 2000); // Scroll down by 2000 pixels
        await wait(1000); // Wait 1 second for posts to load/render
        document.querySelectorAll('shreddit-post').forEach(post => extractPostData(post));
        attempts++;
      }
      console.log(`Finished: Collected ${collectedPosts.size} posts`);
      displayCollectedPosts(Array.from(collectedPosts.values()));
    }
  
    // Display collected posts in a modal overlay with CSV export functionality
    function displayCollectedPosts(posts) {
      // Remove any existing container
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
      posts.forEach((post) => {
        html += `<div style="margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee;">
          <p><strong>Post ID:</strong> ${post.postId}</p>
          <p><strong>Title:</strong> ${post.title}</p>
          <p><strong>Content:</strong> ${post.content}</p>
          <p><strong>Votes:</strong> ${post.score} &nbsp; <strong>Comments:</strong> ${post.comments}</p>
        </div>`;
      });
      html += `<div style="text-align: right;">
        <button id="exportCSV" style="padding: 8px 12px; margin-right: 10px;">Export CSV</button>
        <button id="closeRedditPosts" style="padding: 8px 12px;">Close</button>
      </div>`;
      container.innerHTML = html;
      document.body.appendChild(container);
  
      document.getElementById("closeRedditPosts").onclick = () => container.remove();
      document.getElementById("exportCSV").onclick = () => exportPostsToCSV(posts);
    }
  
    // Export collected post data as a CSV file
    function exportPostsToCSV(posts) {
      let csv = "Post ID,Title,Content,Votes,Comments\n";
      posts.forEach(post => {
        csv += `"${post.postId.replace(/"/g, '""')}","${post.title.replace(/"/g, '""')}","${post.content.replace(/"/g, '""')}","${post.score}","${post.comments}"\n`;
      });
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "reddit_posts.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  
    // Add a floating button to trigger the post collection process
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
      button.onclick = collectPosts;
      btnContainer.appendChild(button);
      document.body.appendChild(btnContainer);
    }
  
    // Initialize the script when the page loads
    window.addEventListener("load", addCollectButton);
  })();
  