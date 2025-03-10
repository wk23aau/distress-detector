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
                    .join('\n');
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
      
        // Extract flair from shadow DOM
        const flairElement = post.shadowRoot
            ?.querySelector('shreddit-post-flair') // Find the flair component
            ?.shadowRoot // Access its shadow root
            ?.querySelector('.flair-content'); // Select the content

        const flair = flairElement 
            ? flairElement.textContent.trim()
            : 'No flair';
      
        // Construct the post data object.
        const postData = { postId, title, content, score, comments, flair };
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
        const modal = document.createElement('div');
        modal.style.cssText = `
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.6);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 10001;
          padding: 1rem;
        `;
      
        const form = `
          <div style="
            background: white;
            border-radius: 16px;
            width: 100%;
            max-width: 500px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            font-family: 'Segoe UI', sans-serif;
          ">
            <h2 style="color: #1a202c; margin-bottom: 1.5rem">Collection Settings</h2>
            
            <div style="display: grid; gap: 1.25rem;">
              <div>
                <label style="color: #4a5568; font-weight: 500">Total Time (minutes)</label>
                <input type="number" id="totalTime" 
                  style="width: 100%; padding: 0.75rem; border: 2px solid #e2e8f0; border-radius: 8px;"
                  placeholder="5"
                  min="1"
                  value="5"
                >
              </div>
              
              <div>
                <label style="color: #4a5568; font-weight: 500">Target Posts</label>
                <input type="number" id="totalPosts" 
                  style="width: 100%; padding: 0.75rem; border: 2px solid #e2e8f0; border-radius: 8px;"
                  placeholder="1000"
                  min="1"
                  value="1000"
                >
              </div>
              
              <div>
                <label style="color: #4a5568; font-weight: 500">Batch Time (minutes)</label>
                <input type="number" id="batchTime" 
                  style="width: 100%; padding: 0.75rem; border: 2px solid #e2e8f0; border-radius: 8px;"
                  placeholder="1"
                  min="1"
                  value="1"
                >
              </div>
              
              <div>
                <label style="color: #4a5568; font-weight: 500">Batch Size</label>
                <input type="number" id="batchSize" 
                  style="width: 100%; padding: 0.75rem; border: 2px solid #e2e8f0; border-radius: 8px;"
                  placeholder="100"
                  min="1"
                  value="100"
                >
              </div>
              
              <div>
                <label style="color: #4a5568; font-weight: 500">Scroll Amount (pixels)</label>
                <select id="scrollBySelect" style="
                  width: 100%;
                  padding: 0.75rem;
                  border: 2px solid #e2e8f0;
                  border-radius: 8px;
                  margin-top: 0.5rem;
                ">
                  <option value="2000">2000 pixels</option>
                  <option value="3000" selected>3000 pixels (default)</option>
                  <option value="4000">4000 pixels</option>
                  <option value="5000">5000 pixels</option>
                  <option value="custom">Custom...</option>
                </select>
                <input type="number" id="customScrollBy" 
                  style="
                    width: 100%;
                    padding: 0.75rem;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    margin-top: 0.5rem;
                    display: none;
                  " 
                  placeholder="Enter custom value"
                >
              </div>
              
              <div style="display: flex; gap: 1rem">
                <button id="startCollection" 
                  style="
                    flex: 1;
                    padding: 1rem;
                    background: #3700B3;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: transform 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                  "
                >Start Collection</button>
                <button id="cancelCollection" 
                  style="
                    flex: 1;
                    padding: 1rem;
                    background: #e53e3e;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: transform 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                  "
                >Cancel</button>
              </div>
            </div>
          </div>
        `;
      
        modal.innerHTML = form;
        document.body.appendChild(modal);
      
        const scrollSelect = modal.querySelector('#scrollBySelect');
        const customInput = modal.querySelector('#customScrollBy');
        const startButton = modal.querySelector('#startCollection');
        const cancelButton = modal.querySelector('#cancelCollection');
      
        scrollSelect.addEventListener('change', () => {
          customInput.style.display = scrollSelect.value === 'custom' ? 'block' : 'none';
          if (scrollSelect.value === 'custom') customInput.focus();
          validate();
        });
      
        const validate = () => {
            let valid = true;
          
            // Validate visible numeric inputs
            const numericInputs = modal.querySelectorAll('input[type="number"]');
            numericInputs.forEach(input => {
              // Skip hidden inputs (like customScrollBy when not selected)
              if (input.offsetParent === null) return;
          
              if (input.value <= 0 || isNaN(input.value)) {
                valid = false;
                input.style.borderColor = '#fc8181';
              } else {
                input.style.borderColor = '#e2e8f0';
              }
            });
          
            // Validate scroll selection
            if (scrollSelect.value === 'custom') {
              if (!customInput.value || parseInt(customInput.value) <= 0) {
                valid = false;
                customInput.style.borderColor = '#fc8181';
              } else {
                customInput.style.borderColor = '#e2e8f0';
              }
            }
          
            startButton.disabled = !valid;
            return valid;
          };
      
        return new Promise(resolve => {
          startButton.addEventListener('click', async () => {
            if (!validate()) return;
      
            const params = {
              totalTime: parseFloat(modal.querySelector('#totalTime').value) * 60000,
              totalPosts: parseInt(modal.querySelector('#totalPosts').value, 10),
              batchTime: parseFloat(modal.querySelector('#batchTime').value) * 60000,
              batchSize: parseInt(modal.querySelector('#batchSize').value, 10),
              scrollBy: scrollSelect.value === 'custom' 
                ? parseInt(customInput.value, 10)
                : parseInt(scrollSelect.value, 10)
            };
      
            modal.remove();
            resolve(params);
          });
      
          cancelButton.addEventListener('click', () => {
            modal.remove();
            resolve(null);
          });
        }).then(async params => {
          if (!params) return;
      
          const {
            totalTime: totalTimeMs,
            totalPosts: targetTotalPosts,
            batchTime: batchTimeMs,
            batchSize,
            scrollBy
          } = params;
      
          const overallStartTime = Date.now();
          let batchStartTime = Date.now();
      
          try {
            while(cumulativeCount < targetTotalPosts && 
                  (Date.now() - overallStartTime) < totalTimeMs) {
              window.scrollBy(0, scrollBy);
              await wait(1000);
              document.querySelectorAll('shreddit-post')
                .forEach(post => extractPostData(post));
      
              if ((Date.now() - batchStartTime) >= batchTimeMs || 
                  currentBatch.length >= batchSize) {
                await autoUploadBatch(currentBatch);
                cumulativeCount += currentBatch.length;
                currentBatch = [];
                batchStartTime = Date.now();
              }
            }
      
            if (currentBatch.length > 0) {
              await autoUploadBatch(currentBatch);
              cumulativeCount += currentBatch.length;
            }
      
            displayCollectedPosts(Array.from(collectedPosts.values()));
          } catch (error) {
            console.error('Collection failed:', error);
            alert('An error occurred during collection. Check console for details.');
          }
        });
      }
    
    // Enhanced Floating Action Button (FAB) Implementation
    function addStylishCollectButton() {
      // Remove any existing buttons to prevent duplicates
      document.querySelectorAll('button.collect-fab').forEach(btn => btn.remove());

      // Create button container
      const btnContainer = document.createElement('div');
      Object.assign(btnContainer.style, {
        position: 'fixed',
        bottom: '2rem',
        right: '2rem',
        zIndex: 10000,
        display: 'flex',
        gap: '1rem'
      });

      // Create main action button
      const button = document.createElement('button');
      button.innerHTML = '🚀 Collect Posts';
      button.className = 'collect-fab';
      
      Object.assign(button.style, {
        padding: '1.25rem 2rem',
        backgroundColor: '#6200ee',
        color: 'white',
        border: 'none',
        borderRadius: '50px',
        cursor: 'pointer',
        fontSize: '1rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.24)',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 500,
        fontFamily: 'Segoe UI, sans-serif'
      });

      // Add hover effects
      button.addEventListener('mouseenter', () => {
        button.style.transform = 'translateY(-4px)';
        button.style.boxShadow = '0 8px 24px rgba(0,0,0,0.24)';
      });

      button.addEventListener('mouseleave', () => {
        button.style.transform = 'translateY(0)';
        button.style.boxShadow = '0 4px 12px rgba(0,0,0,0.24)';
      });

      // Add click effect
      button.addEventListener('mousedown', () => {
        button.style.transform = 'scale(0.98)';
      });

      button.addEventListener('mouseup', () => {
        button.style.transform = 'scale(1)';
      });

      // Attach main functionality
      button.onclick = collectPostsBatched;

      // Add to DOM
      btnContainer.appendChild(button);
      document.body.appendChild(btnContainer);
    }

    // Modern Material Design Modal
    function displayCollectedPosts(posts) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.6);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 10001;
          padding: 1rem;
        `;
      
        const modal = document.createElement('div');
        modal.style.cssText = `
          background: white;
          border-radius: 12px;
          width: 100%;
          max-width: 768px;
          max-height: 90vh;
          overflow: hidden;
          box-shadow: 0 8px 32px rgba(0,0,0,0.3);
          font-family: 'Segoe UI', sans-serif;
        `;
      
        // Header Section
        const header = document.createElement('div');
        header.style.cssText = `
          background: #6200ee;
          color: white;
          padding: 1.5rem;
          border-top-left-radius: 12px;
          border-top-right-radius: 12px;
          display: flex;
          align-items: center;
          gap: 1rem;
        `;
        header.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
            <path fill="white" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
            <path fill="white" d="M11 17h2v-6h-2v6zm0-8h2V7h-2v2z"/>
          </svg>
          <h2 style="margin: 0; flex: 1">Collected ${posts.length} Posts</h2>
          <button id="closeModal" style="
            background: transparent;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
          ">&times;</button>
        `;
      
        // Content Section
        const content = document.createElement('div');
        content.style.cssText = `
          padding: 1.5rem;
          overflow-y: auto;
          max-height: 60vh;
        `;
      
        // Generate HTML for each post, including flair with an icon
        content.innerHTML = posts.map(post => `
          <div style="padding: 1rem; border-bottom: 1px solid #eee">
            <p><strong>🆔 ID:</strong> ${post.postId}</p>
            <p><strong>📌 Title:</strong> ${post.title}</p>
            <p><strong>✨ Flair:</strong> ${post.flair || 'No flair'}</p>
            <p style="color: #555">${post.content}</p>
            <div style="display: flex; gap: 1rem; margin-top: 0.5rem; color: #666;">
              <div>👍 ${post.score}</div>
              <div>💬 ${post.comments}</div>
            </div>
          </div>
        `).join('');
      
        // Action Buttons
        const actions = document.createElement('div');
        actions.style.cssText = `
          display: flex;
          gap: 1rem;
          padding: 1rem;
          background: #f5f5f5;
          border-bottom-left-radius: 12px;
          border-bottom-right-radius: 12px;
        `;
      
        ['CSV', 'JSON'].forEach(format => {
          const btn = document.createElement('button');
          btn.textContent = `Download ${format}`;
          btn.style.cssText = `
            flex: 1;
            padding: 1rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: transform 0.2s;
            background: ${format === 'CSV' ? '#4CAF50' : '#FF9800'};
            color: white;
            display: flex;          /* Added */
            align-items: center;    /* Added */
            justify-content: center; /* Added */
        `;
          btn.addEventListener('click', () => {
            const data = format === 'CSV' 
              ? generateCSVFromArray(posts) 
              : getJSONData(posts);
            const blob = new Blob([data], { type: `application/${format.toLowerCase()}` });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `posts_${getHumanReadableTimestamp()}.${format.toLowerCase()}`;
            link.click();
          });
          actions.appendChild(btn);
        });
      
        // Assemble modal
        modal.appendChild(header);
        modal.appendChild(content);
        modal.appendChild(actions);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
      
        // Close handlers
        document.getElementById('closeModal').addEventListener('click', () => overlay.remove());
        overlay.addEventListener('click', (e) => e.target === overlay && overlay.remove());
      }

    // Initialization
    window.addEventListener('load', () => {
        addStylishCollectButton();
    });
})();