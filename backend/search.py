
from pathlib import Path
import re

import numpy as np
import pandas as pd
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer


BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "data" / "search_index"

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Existing search index
chunks_df = pd.read_csv(INDEX_DIR / "chunks.csv")
embeddings = np.load(INDEX_DIR / "embeddings.npy")

assert len(chunks_df) == len(embeddings), (
    "Number of chunks and embeddings doesn't match!"
)

# Download the ONNX model and tokenizer from the same model repository.
model_path = hf_hub_download(
    repo_id=MODEL_ID,
    filename="onnx/model.onnx",
)

tokenizer_path = hf_hub_download(
    repo_id=MODEL_ID,
    filename="tokenizer.json",
)

tokenizer = Tokenizer.from_file(tokenizer_path)
tokenizer.enable_truncation(max_length=256)
tokenizer.enable_padding()

session = ort.InferenceSession(
    model_path,
    sess_options=ort.SessionOptions(),
    providers=["CPUExecutionProvider"],
)

input_names = {item.name for item in session.get_inputs()}

print(
    f"Loaded {len(chunks_df)} chunks from "
    f"{chunks_df['video_id'].nunique()} episodes!"
)


def encode_texts(texts):
    """Generate normalized sentence embeddings using ONNX."""
    single_input = isinstance(texts, str)

    if single_input:
        texts = [texts]

    encoded = tokenizer.encode_batch(list(texts))

    input_ids = np.asarray(
        [item.ids for item in encoded],
        dtype=np.int64,
    )
    attention_mask = np.asarray(
        [item.attention_mask for item in encoded],
        dtype=np.int64,
    )

    model_inputs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }

    if "token_type_ids" in input_names:
        model_inputs["token_type_ids"] = np.asarray(
            [item.type_ids for item in encoded],
            dtype=np.int64,
        )

    outputs = session.run(None, model_inputs)

    # SentenceTransformer's mean pooling over token embeddings.
    token_embeddings = outputs[0]

    mask = attention_mask[:, :, None].astype(np.float32)

    summed = (token_embeddings * mask).sum(axis=1)
    counts = np.maximum(mask.sum(axis=1), 1e-9)

    sentence_embeddings = summed / counts

    # Normalize so dot product equals cosine similarity.
    norms = np.linalg.norm(
        sentence_embeddings,
        axis=1,
        keepdims=True,
    )
    sentence_embeddings = sentence_embeddings / np.maximum(
        norms, 1e-12
    )

    sentence_embeddings = sentence_embeddings.astype(np.float32)

    if single_input:
        return sentence_embeddings[0]

    return sentence_embeddings


def format_timestamp(seconds):
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes}:{seconds:02d}"


def clean_preview(text, max_chars=300):
    text = re.sub(r">>", " ", str(text))
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "..."

    return text


def make_smart_preview(query_embedding, text, window_words=35):
    text = clean_preview(text, max_chars=10000)
    words = text.split()

    if len(words) <= window_words:
        return text

    step = max(1, window_words // 2)

    windows = [
        " ".join(words[i:i + window_words])
        for i in range(0, len(words), step)
        if len(words[i:i + window_words]) >= 15
    ]

    window_embeddings = encode_texts(windows)
    scores = window_embeddings @ query_embedding

    best_index = int(np.argmax(scores))
    return windows[best_index]


def search_podcast(query, top_k=5):
    query_embedding = encode_texts(query)

    scores = embeddings @ query_embedding
    ranked_indices = np.argsort(scores)[::-1]

    results = []
    seen_episodes = set()

    for idx in ranked_indices:
        row = chunks_df.iloc[int(idx)]
        video_id = str(row["video_id"])

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
            "preview": make_smart_preview(
                query_embedding,
                row["text"],
            ),
            "url": (
                "https://www.youtube.com/watch?"
                f"v={video_id}&t={int(start)}s"
            ),
        })

        if len(results) >= top_k:
            break

    return results
