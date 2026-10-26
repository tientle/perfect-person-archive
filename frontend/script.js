const form = document.querySelector("#search-form");
const input = document.querySelector("#search-input");
const results = document.querySelector("#results");

// Our local FastAPI server
const API_URL = "https://perfect-person-archive.onrender.com";

// Format a numerical similarity score for display
function formatSimilarity(score) {
  return Number(score).toFixed(3);
}

// Create a result card for one podcast match
function createResultCard(match) {
  const card = document.createElement("article");
  card.className = "result-card";

  // Only allow links to actual YouTube videos
  const videoId = String(match.video_id);

  const youtubeUrl = new URL("https://www.youtube.com/watch");
  youtubeUrl.searchParams.set("v", videoId);
  youtubeUrl.searchParams.set("t", `${Math.floor(match.start)}s`);

  // Top row: episode label and timestamp
  const top = document.createElement("div");
  top.className = "result-top";

  const episodeLabel = document.createElement("span");
  episodeLabel.className = "episode-label";
  episodeLabel.textContent = "PERFECT PERSON";

  const timestamp = document.createElement("span");
  timestamp.className = "timestamp-badge";
  timestamp.textContent = match.timestamp;

  top.append(episodeLabel, timestamp);

  // Clickable episode title
  const title = document.createElement("h3");
  title.className = "result-title";

  const titleLink = document.createElement("a");
  titleLink.href = youtubeUrl.toString();
  titleLink.target = "_blank";
  titleLink.rel = "noopener noreferrer";
  titleLink.textContent = match.episode;

  const arrow = document.createElement("span");
  arrow.textContent = " ↗";
  arrow.setAttribute("aria-hidden", "true");

  titleLink.appendChild(arrow);
  title.appendChild(titleLink);

  // Transcript preview
  const preview = document.createElement("p");
  preview.className = "result-preview";
  preview.textContent = `“${match.preview}”`;

  // Footer: cosine similarity and listen link
  const footer = document.createElement("div");
  footer.className = "result-footer";

  const similarityInfo = document.createElement("div");
  similarityInfo.className = "similarity-info";

  const similarityText = document.createElement("span");
  similarityText.textContent =
    `Cosine similarity: ${formatSimilarity(match.similarity)}`;

  // Accessible explanation of cosine similarity
  const tooltip = document.createElement("span");
  tooltip.className = "similarity-tooltip";
  tooltip.tabIndex = 0;
  tooltip.textContent = "ⓘ";
  tooltip.setAttribute(
    "aria-label",
    "About cosine similarity"
  );

  const tooltipText = document.createElement("span");
  tooltipText.className = "tooltip-text";
  tooltipText.textContent =
    "Cosine similarity measures how closely the search query " +
    "and transcript passage align in embedding space. " +
    "Higher scores indicate closer matches, not a percentage of relevance.";

  tooltip.appendChild(tooltipText);
  similarityInfo.append(similarityText, tooltip);

  // Timestamped YouTube link
  const listenLink = document.createElement("a");
  listenLink.className = "listen-link";
  listenLink.href = youtubeUrl.toString();
  listenLink.target = "_blank";
  listenLink.rel = "noopener noreferrer";
  listenLink.textContent = `▶ Listen at ${match.timestamp}`;

  footer.append(similarityInfo, listenLink);

  // Assemble card
  card.append(top, title, preview, footer);

  return card;
}

// Handle search submissions
form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const query = input.value.trim();
  if (!query) return;

  results.replaceChildren();


const loading = document.createElement("div");
loading.className = "search-loading";
loading.setAttribute("role", "status");

const spinner = document.createElement("span");
spinner.className = "loading-spinner";
spinner.setAttribute("aria-hidden", "true");

const message = document.createElement("div");

const loadingTitle = document.createElement("p");
loadingTitle.className = "loading-title";
loadingTitle.textContent = "Searching the archive... ♡";

const loadingSubtitle = document.createElement("p");
loadingSubtitle.className = "loading-subtitle";
loadingSubtitle.textContent = "This can take a moment!";

message.append(loadingTitle, loadingSubtitle);
loading.append(spinner, message);
results.appendChild(loading);


  try {
    const response = await fetch(
      `${API_URL}/search?query=${encodeURIComponent(query)}`
    );

    if (!response.ok) {
      throw new Error("Search request failed");
    }

    const matches = await response.json();
    results.replaceChildren();

    if (matches.length === 0) {
      results.textContent =
        "No matching moments found in the current archive. ♡";
      return;
    }

    matches.forEach((match) => {
      const card = createResultCard(match);
      results.appendChild(card);
    });

  } catch (error) {
    results.textContent =
      "Couldn't connect to the search API. Is FastAPI running?";
    console.error(error);
  }
});

// Load archive progress from FastAPI
async function loadArchiveProgress() {
  try {
    const response = await fetch(`${API_URL}/stats`);

    if (!response.ok) {
      throw new Error("Could not load archive stats");
    }

    const stats = await response.json();

    document.getElementById("indexed-count").textContent =
      stats.indexed_episodes;

    document.getElementById("total-count").textContent =
      stats.total_episodes;

    document.getElementById("progress-percentage").textContent =
      `${stats.percentage}%`;

    document.getElementById("progress-fill").style.width =
      `${stats.percentage}%`;

    document.getElementById("archive-progress-bar")
      .setAttribute("aria-valuenow", stats.percentage);

  } catch (error) {
    console.error("Error loading archive progress:", error);
  }
}

document.addEventListener("DOMContentLoaded", loadArchiveProgress);
