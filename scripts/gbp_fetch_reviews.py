#!/usr/bin/env python3
"""
Fetches Google reviews for FastFix Locksmith Brisbane's Business Profile and
drops any review that doesn't have a reply yet, and that we haven't already
queued, into reviews/pending/<reviewId>.json for Claude to draft a reply to.

Run by the gbp-reviews.yml workflow on a schedule. Claude's own daily
check-in task pulls this repo, reads reviews/pending/*.json, drafts replies,
and sends them to Stav for approval in chat — nothing here posts a reply
automatically.
"""
import json
import sys
from pathlib import Path

from gbp_common import gbp_get, get_access_token, location_path

ROOT = Path(__file__).resolve().parent.parent
PENDING_DIR = ROOT / "reviews" / "pending"
REPLY_QUEUE_DIR = ROOT / "reviews" / "reply-queue"  # Claude's drafted + approved reply
REPLIED_DIR = ROOT / "reviews" / "replied"


def already_tracked(review_id: str) -> bool:
    for d in (PENDING_DIR, REPLY_QUEUE_DIR, REPLIED_DIR):
        if (d / f"{review_id}.json").exists():
            return True
    return False


def main() -> int:
    for d in (PENDING_DIR, REPLY_QUEUE_DIR, REPLIED_DIR):
        d.mkdir(parents=True, exist_ok=True)

    access_token = get_access_token()

    new_count = 0
    page_token = None
    while True:
        params = {"pageSize": 50}
        if page_token:
            params["pageToken"] = page_token
        data = gbp_get(f"{location_path()}/reviews", access_token, params=params)

        for review in data.get("reviews", []):
            review_id = review["reviewId"]
            has_reply = bool(review.get("reviewReply"))
            if has_reply or already_tracked(review_id):
                continue
            out = PENDING_DIR / f"{review_id}.json"
            out.write_text(json.dumps(review, indent=2, ensure_ascii=False))
            new_count += 1
            print(f"NEW REVIEW: {review_id} ({review.get('starRating')}) -> {out}")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    print(f"Done. {new_count} new review(s) queued for reply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
