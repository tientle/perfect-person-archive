
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# 1. Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
INDEX_DIR = DATA_DIR / "search_index"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

# 2. Load episode metadata
episodes = pd.read_csv(DATA_DIR / "episodes.csv")
episode_lookup = episodes.set_index("video_id")

# 3. Read transcripts and create chunks
chunks = []
indexed_episodes = set()

for transcript_path in sorted(TRANSCRIPT_DIR.glob("*.json")):
    video_id = transcript_path.stem

    if video_id not in episode_lookup.index:
        print(f"SKIP unknown video ID: {video_id}")
        continue

    try:
        with open(transcript_path, encoding="utf-8") as f:
            segments = json.load(f)

        if not isinstance(segments, list) or not segments:
            print(f"SKIP empty transcript: {video_id}")
            continue

        title = str(episode_lookup.loc[video_id, "title"])

        # Build a word stream while retaining timestamps
        word_stream = []

        for segment in segments:
            text = str(segment.get("text", "")).strip()
            start = float(segment.get("start", 0))

            for word in text.split():
                word_stream.append((word, start))

        if not word_stream:
            continue

        # Fixed-size chunks: 150 words, 30-word overlap
        chunk_size = 150
        overlap = 30
        step = chunk_size - overlap

        for i in range(0, len(word_stream), step):
            window = word_stream[i:i + chunk_size]

            if len(window) < 30:
                continue

            chunks.append({
                "video_id": video_id,
                "title": title,
                "start": window[0][1],
                "text": " ".join(word for word, _ in window),
            })

        indexed_episodes.add(video_id)

    except (OSError, ValueError, TypeError, KeyError) as e:
        print(f"SKIP invalid transcript {video_id}: {e}")

# 4. Convert chunks to a DataFrame
chunks_df = pd.DataFrame(chunks)

if chunks_df.empty:
    raise RuntimeError("No valid transcript chunks were created.")

print(f"Loaded {len(indexed_episodes)} episodes")
print(f"Created {len(chunks_df)} chunks")

# 5. Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(
    chunks_df["text"].tolist(),
    normalize_embeddings=True,
    show_progress_bar=True,
)

# 6. Save the updated search index
chunks_df.to_csv(
    INDEX_DIR / "chunks.csv",
    index=False
)

np.save(
    INDEX_DIR / "embeddings.npy",
    embeddings
)

print("\nSearch index updated!")
print(f"Episodes indexed: {len(indexed_episodes)}")
print(f"Chunks saved: {len(chunks_df)}")
print(f"Embeddings shape: {embeddings.shape}")
