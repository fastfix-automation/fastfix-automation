#!/usr/bin/env python3
"""
Publishes queued posts ("What's New" updates) to the FastFix Locksmith
Brisbane Google Business Profile.

How it works (mirrors scripts/publish.py for FB/IG):
  - Each file in gbp_queue/*.json describes one post:
      {
        "summary": "...",                                  # post text
        "image_url": "https://.../image.jpg",               # public https url
        "cta": {"actionType": "CALL", "url": null},          # optional, see below
        "publish_at": "2026-10-12T23:00:00Z"                 # optional, UTC
      }
  - image_url must be public (Google fetches it directly) — same docs/images/
    GitHub Pages setup already used for FB/IG.
  - cta.actionType is one of Google's allowed values, e.g. CALL, LEARN_MORE,
    BOOK, ORDER, SHOP, SIGN_UP — CALL needs no url (uses the listed phone
    number), the others require one. Omit "cta" entirely for a plain update
    with no button.
  - On success, the file moves to gbp_published/. On failure, to gbp_failed/
    with the error attached (and the job fails, same retry-safe pattern as
    the FB/IG pipeline).
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from gbp_common import get_access_token, gbp_post, location_path

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "gbp_queue"
PUBLISHED_DIR = ROOT / "gbp_published"
FAILED_DIR = ROOT / "gbp_failed"


def is_due(post: dict) -> bool:
    publish_at = post.get("publish_at")
    if not publish_at:
        return True
    scheduled = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) >= scheduled


def build_local_post_body(post: dict) -> dict:
    body = {
        "languageCode": "en-AU",
        "summary": post["summary"],
        "topicType": "STANDARD",
        "media": [{"mediaFormat": "PHOTO", "sourceUrl": post["image_url"]}],
    }
    if post.get("cta"):
        body["callToAction"] = post["cta"]
    return body


def process_file(path: Path, access_token: str) -> dict:
    post = json.loads(path.read_text())
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    try:
        result = gbp_post(
            f"{location_path()}/localPosts",
            access_token,
            build_local_post_body(post),
        )
    except Exception as e:  # noqa: BLE001
        post["error"] = str(e)
        (FAILED_DIR / f"{timestamp}-{path.name}").write_text(
            json.dumps(post, indent=2, ensure_ascii=False)
        )
        path.unlink()
        print(f"FAILED: {path.name} -> {e}")
        return {"error": str(e)}

    post["result"] = result
    (PUBLISHED_DIR / f"{timestamp}-{path.name}").write_text(
        json.dumps(post, indent=2, ensure_ascii=False)
    )
    path.unlink()
    print(f"PUBLISHED: {path.name} -> {result.get('name', result)}")
    return {}


def main() -> int:
    for d in (QUEUE_DIR, PUBLISHED_DIR, FAILED_DIR):
        d.mkdir(parents=True, exist_ok=True)

    queue_files = sorted(QUEUE_DIR.glob("*.json"))
    if not queue_files:
        print("No queued GBP posts.")
        return 0

    access_token = get_access_token()
    had_error = False

    for f in queue_files:
        post = json.loads(f.read_text())
        if not is_due(post):
            print(f"SCHEDULED (not due yet): {f.name} -> publish_at={post.get('publish_at')}")
            continue
        result = process_file(f, access_token)
        if result.get("error"):
            had_error = True

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
