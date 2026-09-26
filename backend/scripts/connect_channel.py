"""Connect a YouTube channel so the engine can use its verified analytics.

Run this once per channel, by whoever owns it:

    python scripts/connect_channel.py

It opens a Google consent screen, then writes the token to
`backend/.tokens/<channel_id>.json`. From that point the engine reports that
channel's audience data as VERIFIED instead of ESTIMATED.

Requires GOOGLE_OAUTH_CLIENT_SECRETS in .env, pointing at the OAuth client
JSON downloaded from Google Cloud Console (see SETUP.md). Until an app is
verified by Google it is limited to 100 test users, which is ample for a
demo but means this is not yet a public sign-up flow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.providers.analytics.oauth import TOKEN_DIR  # noqa: E402

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def main() -> int:
    settings = get_settings()
    if not settings.google_oauth_client_secrets:
        print("GOOGLE_OAUTH_CLIENT_SECRETS is not set — see SETUP.md phase 4.")
        return 1

    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    flow = InstalledAppFlow.from_client_secrets_file(
        settings.google_oauth_client_secrets, SCOPES
    )
    creds = flow.run_local_server(port=8765, prompt="consent")

    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    channels = youtube.channels().list(part="snippet", mine=True).execute().get("items", [])
    if not channels:
        print("That account does not own a YouTube channel.")
        return 1

    channel = channels[0]
    channel_id = channel["id"]
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    (TOKEN_DIR / f"{channel_id}.json").write_text(creds.to_json())
    (TOKEN_DIR / f"{channel_id}.meta.json").write_text(
        json.dumps(
            {
                "title": channel["snippet"]["title"],
                "country": channel["snippet"].get("country", "US"),
            },
            indent=2,
        )
    )
    print(f"Connected: {channel['snippet']['title']} ({channel_id})")
    print(f"Token written to {TOKEN_DIR}")
    print("Set ANALYTICS_MODE=oauth to use verified audience data for this channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
