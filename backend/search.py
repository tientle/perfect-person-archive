
from pathlib import Path
import re

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Find the project root
BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "data" / "search_index"

# Load our new 29-episode search index
chunks_df = pd.read_csv(INDEX_DIR / "chunks.csv")
embeddings = np.load(INDEX_DIR / "embeddings.npy")

# Same embedding model used in the notebook
model = SentenceTransformer("all-MiniLM-L6-v2")

# Check that chunks and embeddings align
assert len(chunks_df) == len(embeddings), (
    "Number of chunks and embeddings doesn't match!"
)

print(
    f"Loaded {len(chunks_df)} chunks from "
    f"{chunks_df['video_id'].nunique()} episodes!"
)


def format_timestamp(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


def clean_preview(text, max_chars=300):
    text = re.sub(r">>", " ", str(text))
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "..."

    return text

def make_smart_preview(query_embedding, text, window_words=35):
    # Clean the transcript text
    text = re.sub(r">>", " ", str(text))
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    if len(words) <= window_words:
        return text

    # Create overlapping windows
    step = max(1, window_words // 2)

    windows = [
        " ".join(words[i:i + window_words])
        for i in range(0, len(words), step)
        if len(words[i:i + window_words]) >= 15
    ]

    # Embed each smaller passage
    window_embeddings = model.encode(
        windows,
        normalize_embeddings=True
    )

    # Find the window most similar to the query
    scores = window_embeddings @ query_embedding
    best_index = np.argmax(scores)

    return windows[best_index]


def search_podcast(query, top_k=5):
    # Convert the user's query into an embedding
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    # Compare the query to all saved chunks
    scores = embeddings @ query_embedding

    # Rank from highest similarity to lowest
    ranked_indices = np.argsort(scores)[::-1]

    results = []
    seen_episodes = set()

    for idx in ranked_indices:
        row = chunks_df.iloc[int(idx)]
        video_id = str(row["video_id"])

        # Return only one passage per episode
        if video_id in seen_episodes:
            continue

        seen_episodes.add(video_id)

        start = float(row["start"])

        results.append({
            "episode": str(row["title"]),
            "video_id": video_id,
            "start": start,
            "timestamp": format_timestamp(start),
            "similarity": round(float(scores[idx]), 3),
            "preview": make_smart_preview(query_embedding, row["text"]),
            "url": (
                f"https://www.youtube.com/watch?"
                f"v={video_id}&t={int(start)}s"
            )
        })

        if len(results) >= top_k:
            break

    return results
