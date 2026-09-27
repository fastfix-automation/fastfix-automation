#!/usr/bin/env python3
"""
FastFix social automation — publishes queued posts to Facebook Page + Instagram
via the Meta Graph API.

How it works:
  - Each file in queue/*.json describes one post: {"caption": "...", "image_url": "https://.../image.jpg", "targets": ["facebook", "instagram"]}
  - image_url must be a PUBLIC https url (Meta's servers fetch it directly) — that's
    what the docs/images/ + GitHub Pages folder is for.
  - On success, the queue file is moved to published/<timestamp>-<name>.json
  - On failure, it's moved to failed/<timestamp>-<name>.json with the error attached,
    and the job fails (so it shows up as a red X in GitHub Actions / triggers a
    notification you can see).

Secrets required (set in repo Settings > Secrets and variables > Actions):
  - META_PAGE_ACCESS_TOKEN : the Page Access Token (never-expire, from the System User)
  - FB_PAGE_ID             : Facebook Page ID
  - IG_USER_ID             : Instagram Business Account ID
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

GRAPH_API = "https://graph.facebook.com/v21.0"

PAGE_TOKEN = os.environ["META_PAGE_ACCESS_TOKEN"]
FB_PAGE_ID = os.environ["FB_PAGE_ID"]
IG_USER_ID = os.environ["IG_USER_ID"]

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "queue"
PUBLISHED_DIR = ROOT / "published"
FAILED_DIR = ROOT / "failed"


def publish_to_facebook(caption: str, image_url: str) -> str:
    resp = requests.post(
        f"{GRAPH_API}/{FB_PAGE_ID}/photos",
        data={"url": image_url, "caption": caption, "access_token": PAGE_TOKEN},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("post_id") or resp.json().get("id")


def publish_to_instagram(caption: str, image_url: str) -> str:
    create = requests.post(
        f"{GRAPH_API}/{IG_USER_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": PAGE_TOKEN},
        timeout=60,
    )
    create.raise_for_status()
    creation_id = create.json()["id"]

    # IG sometimes needs a moment to finish processing the image before publish.
    time.sleep(3)

    publish = requests.post(
        f"{GRAPH_API}/{IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": PAGE_TOKEN},
        timeout=60,
    )
    publish.raise_for_status()
    return publish.json()["id"]


def is_due(post: dict) -> bool:
    """A post with no publish_at is due immediately. A post with publish_at (ISO 8601,
    e.g. "2026-09-29T23:00:00Z" for Brisbane time converted to UTC) is only due once
    that time has passed."""
    publish_at = post.get("publish_at")
    if not publish_at:
        return True
    scheduled = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) >= scheduled


def process_file(path: Path) -> None:
    post = json.loads(path.read_text())
    caption = post["caption"]
    image_url = post["image_url"]
    targets = post.get("targets", ["facebook", "instagram"])

    results = {}
    errors = {}

    if "facebook" in targets:
        try:
            results["facebook_post_id"] = publish_to_facebook(caption, image_url)
        except Exception as e:  # noqa: BLE001
            errors["facebook"] = str(e)

    if "instagram" in targets:
        try:
            results["instagram_media_id"] = publish_to_instagram(caption, image_url)
        except Exception as e:  # noqa: BLE001
            errors["instagram"] = str(e)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    if errors:
        post["errors"] = errors
        post["partial_results"] = results
        dest = FAILED_DIR / f"{timestamp}-{path.name}"
        dest.write_text(json.dumps(post, indent=2, ensure_ascii=False))
        path.unlink()
        print(f"FAILED: {path.name} -> {errors}")
    else:
        post["results"] = results
        dest = PUBLISHED_DIR / f"{timestamp}-{path.name}"
        dest.write_text(json.dumps(post, indent=2, ensure_ascii=False))
        path.unlink()
        print(f"PUBLISHED: {path.name} -> {results}")

    return errors


def main() -> int:
    queue_files = sorted(QUEUE_DIR.glob("*.json"))
    if not queue_files:
        print("No queued posts.")
        return 0

    had_error = False
    for f in queue_files:
        post = json.loads(f.read_text())
        if not is_due(post):
            print(f"SCHEDULED (not due yet): {f.name} -> publish_at={post.get('publish_at')}")
            continue
        errors = process_file(f)
        if errors:
            had_error = True

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
