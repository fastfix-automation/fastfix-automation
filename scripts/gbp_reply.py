#!/usr/bin/env python3
"""
Posts approved review replies to Google and files the result.

How it works:
  - Claude drafts a reply for a review in reviews/pending/<reviewId>.json and,
    once Stav approves it in chat, writes reviews/reply-queue/<reviewId>.json:
      {"review_id": "...", "reply_text": "..."}
  - Pushing that file to main triggers the gbp-reviews.yml workflow, which runs
    this script.
  - On success: the reply-queue file and the matching pending file are both
    removed, and a combined record (review + reply) is written to
    reviews/replied/<reviewId>.json.
  - On failure: the reply-queue file is left in place (and the error is
    printed) so the next run retries it; nothing is silently dropped.
"""
import json
import sys
from pathlib import Path

from gbp_common import get_access_token, gbp_put, location_path

ROOT = Path(__file__).resolve().parent.parent
PENDING_DIR = ROOT / "reviews" / "pending"
REPLY_QUEUE_DIR = ROOT / "reviews" / "reply-queue"
REPLIED_DIR = ROOT / "reviews" / "replied"


def main() -> int:
    for d in (PENDING_DIR, REPLY_QUEUE_DIR, REPLIED_DIR):
        d.mkdir(parents=True, exist_ok=True)

    queue_files = sorted(REPLY_QUEUE_DIR.glob("*.json"))
    if not queue_files:
        print("No approved replies waiting to post.")
        return 0

    access_token = get_access_token()
    had_error = False

    for f in queue_files:
        item = json.loads(f.read_text())
        review_id = item["review_id"]
        reply_text = item["reply_text"]
        try:
            gbp_put(
                f"{location_path()}/reviews/{review_id}/reply",
                access_token,
                {"comment": reply_text},
            )
        except Exception as e:  # noqa: BLE001
            print(f"FAILED to reply to {review_id}: {e}")
            had_error = True
            continue

        pending_file = PENDING_DIR / f"{review_id}.json"
        review_data = json.loads(pending_file.read_text()) if pending_file.exists() else {}
        record = {"review": review_data, "reply_text": reply_text}
        (REPLIED_DIR / f"{review_id}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False)
        )
        pending_file.unlink(missing_ok=True)
        f.unlink()
        print(f"REPLIED: {review_id}")

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
