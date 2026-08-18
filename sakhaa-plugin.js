// sakhaa-plugin.js
(function () {
  const API_URL = "https://sakhaa.samvadah.workers.dev/";

  // 1. Mobile-friendly CSS
  const style = document.createElement("style");
  style.innerHTML = `
    #sakha-tooltip {
      position: absolute;
      background: #ffffff;
      color: #1e293b;
      border: 1px solid #cbd5e1;
      padding: 10px 14px;
      border-radius: 8px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Devanagari", sans-serif;
      font-size: 15px;
      line-height: 1.5;
      z-index: 999999;
      display: none;
      max-width: 90vw;
      width: max-content;
      word-wrap: break-word;
      box-sizing: border-box;
    }
    #sakha-tooltip .sakha-header {
      font-weight: bold;
      color: #0f172a;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 4px;
      font-size: 13px;
    }
    #sakha-tooltip .sakha-close {
      cursor: pointer;
      color: #94a3b8;
      font-size: 18px;
      line-height: 1;
      padding: 0 4px;
    }
    #sakha-tooltip .sakha-close:hover {
      color: #ef4444;
    }
    #sakha-tooltip .sakha-content {
      color: #1d4ed8;
      font-weight: bold;
    }
    #sakha-tooltip .sakha-loading {
      color: #64748b;
      font-style: italic;
    }
  `;
  document.head.appendChild(style);

  // 2. Create the Tooltip Element
  const tooltip = document.createElement("div");
  tooltip.id = "sakha-tooltip";
  document.body.appendChild(tooltip);

  let lastSelectedText = "";

  async function handleSelection() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const selectedText = selection.toString().trim();
    if (!selectedText || selectedText.length > 150) return;
    if (selectedText === lastSelectedText && tooltip.style.display === "block") return;

    lastSelectedText = selectedText;

    // Get exact screen position of the highlighted text (works on mobile + desktop)
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    if (!rect || rect.width === 0) return;

    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;

    // Position tooltip right below the highlighted text
    let top = rect.bottom + scrollY + 8;
    let left = rect.left + scrollX;

    // Boundary check so it stays inside mobile screen widths
    const maxLeft = window.innerWidth - 320;
    if (left > maxLeft && maxLeft > 10) {
      left = maxLeft;
    }
    if (left < 10) left = 10;

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
    tooltip.style.display = "block";
    tooltip.innerHTML = `
      <div class="sakha-header">
        <span>सखा • पदच्छेदः</span>
        <span class="sakha-close" id="sakha-close-btn">&times;</span>
      </div>
      <div class="sakha-loading">विश्लेषणं प्रचलति...</div>
    `;

    document.getElementById("sakha-close-btn").onclick = () => {
      tooltip.style.display = "none";
      lastSelectedText = "";
    };

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: selectedText }),
      });

      const data = await response.json();

      if (data && data.segmentation) {
        tooltip.innerHTML = `
          <div class="sakha-header">
            <span>सखा • पदच्छेदः</span>
            <span class="sakha-close" id="sakha-close-btn">&times;</span>
          </div>
          <div class="sakha-content">${data.segmentation}</div>
        `;
      } else {
        tooltip.innerHTML = `
          <div class="sakha-header">
            <span>सखा</span>
            <span class="sakha-close" id="sakha-close-btn">&times;</span>
          </div>
          <div style="color: #64748b;">No segmentation found.</div>
        `;
      }

      document.getElementById("sakha-close-btn").onclick = () => {
        tooltip.style.display = "none";
        lastSelectedText = "";
      };
    } catch (err) {
      tooltip.innerHTML = `
        <div class="sakha-header">
          <span>सखा</span>
          <span class="sakha-close" id="sakha-close-btn">&times;</span>
        </div>
        <div style="color: #ef4444;">Analysis failed.</div>
      `;
      document.getElementById("sakha-close-btn").onclick = () => {
        tooltip.style.display = "none";
        lastSelectedText = "";
      };
    }
  }

  // Desktop listener
  document.addEventListener("mouseup", function (e) {
    if (tooltip.contains(e.target)) return;
    setTimeout(handleSelection, 50);
  });

  // Mobile / Touchscreen listener
  document.addEventListener("touchend", function (e) {
    if (tooltip.contains(e.target)) return;
    // Small delay to allow mobile selection handles to finish expanding
    setTimeout(handleSelection, 200);
  });

  // Dismiss on tap/click elsewhere
  document.addEventListener("mousedown", function (e) {
    if (tooltip.style.display === "block" && !tooltip.contains(e.target)) {
      tooltip.style.display = "none";
      lastSelectedText = "";
    }
  });

  document.addEventListener("touchstart", function (e) {
    if (tooltip.style.display === "block" && !tooltip.contains(e.target)) {
      tooltip.style.display = "none";
      lastSelectedText = "";
    }
  });
})();
