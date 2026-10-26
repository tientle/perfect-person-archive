
from pathlib import Path
import json
import random
import time

import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import RequestBlocked, IpBlocked

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"

TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

# Load episode list
episodes = pd.read_csv(DATA_DIR / "episodes.csv")

print(f"Found {len(episodes)} episodes in playlist.")

api = YouTubeTranscriptApi()
results = []

try:
    for i, episode in episodes.iterrows():
        video_id = str(episode["video_id"])
        title = str(episode["title"])
        output_path = TRANSCRIPT_DIR / f"{video_id}.json"

        # Skip episodes we've already downloaded
        if output_path.exists():
            print(f"[{i+1}/{len(episodes)}] SKIP: {title}")

            results.append({
                "video_id": video_id,
                "status": "existing"
            })
            continue

        try:
            # Fetch transcript
            transcript = api.fetch(video_id).to_raw_data()

            # Add episode metadata
            for segment in transcript:
                segment["video_id"] = video_id
                segment["episode_title"] = title
                segment["url"] = (
                    f"https://www.youtube.com/watch?v={video_id}"
                )

            # Save transcript
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    transcript,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(f"[{i+1}/{len(episodes)}] OK: {title}")

            results.append({
                "video_id": video_id,
                "status": "success",
                "segments": len(transcript)
            })

            # Pause between successful requests
            time.sleep(random.uniform(2, 4))

        except (RequestBlocked, IpBlocked) as e:
            print(
                f"\nYouTube blocked further requests: "
                f"{type(e).__name__}"
            )
            print(
                "Stopping collection. "
                "Already saved transcripts are safe."
            )

            results.append({
                "video_id": video_id,
                "status": "blocked",
                "error": str(e)
            })

            break

        except Exception as e:
            print(f"[{i+1}/{len(episodes)}] FAILED: {title}")
            print(f"    {type(e).__name__}: {e}")

            results.append({
                "video_id": video_id,
                "status": "failed",
                "error": str(e)
            })

except KeyboardInterrupt:
    print("\nDownload interrupted by user.")

finally:
    # Save progress even if the script is interrupted
    pd.DataFrame(results).to_csv(
        DATA_DIR / "transcript_download_log.csv",
        index=False
    )

    saved_count = len(list(TRANSCRIPT_DIR.glob("*.json")))

    print("\nCollection stopped.")
    print(f"Transcripts currently saved: {saved_count}")
    print(f"Total episodes in playlist: {len(episodes)}")
    print(f"Remaining: {max(0, len(episodes) - saved_count)}")
    print("Download log saved.")
