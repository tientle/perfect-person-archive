
from pathlib import Path
import pandas as pd

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"

# Load the complete episode list
episodes = pd.read_csv(DATA_DIR / "episodes.csv")

# Check whether each episode already has a transcript
episodes["has_transcript"] = episodes["video_id"].apply(
    lambda video_id: (
        TRANSCRIPT_DIR / f"{video_id}.json"
    ).exists()
)

# Separate collected and missing episodes
collected = episodes[episodes["has_transcript"]]
missing = episodes[~episodes["has_transcript"]].copy()

# Save missing episodes to a separate CSV
missing = missing.drop(columns=["has_transcript"])

output_path = DATA_DIR / "missing_episodes.csv"
missing.to_csv(output_path, index=False)

# Print a summary
print(f"Total episodes: {len(episodes)}")
print(f"Transcripts collected: {len(collected)}")
print(f"Transcripts missing: {len(missing)}")

print("\nNext 29 missing episodes:")
print(missing[["title", "video_id"]].head(29).to_string(index=False))
print(f"\nMissing episode list saved to: {output_path}")
