# FastFix Automation

Publishes posts to the FastFix Locksmith Brisbane Facebook Page + Instagram
Business account, via the Meta Graph API.

## How posts get published
1. A JSON file is added to `queue/` (Claude does this after you approve a caption in chat).
2. Pushing that file to `main` triggers the `publish.yml` GitHub Action.
3. The action runs `scripts/publish.py`, which posts to Facebook + Instagram.
4. The queue file moves to `published/` (success) or `failed/` (with the error) automatically.

## One-time setup (see chat for the walkthrough)
- Secrets (Settings > Secrets and variables > Actions): `META_PAGE_ACCESS_TOKEN`, `FB_PAGE_ID`, `IG_USER_ID`
- Settings > Actions > General > Workflow permissions: "Read and write permissions"
- Settings > Pages: Source = `main` branch, `/docs` folder (serves images publicly for the API to fetch)

## Queue file format
```json
{
  "caption": "Locked out in Milton? We're there in 15 minutes. 🔑",
  "image_url": "https://<username>.github.io/fastfix-automation/images/job1.jpg",
  "targets": ["facebook", "instagram"],
  "publish_at": "2026-09-29T23:00:00Z"
}
```
`publish_at` is optional (ISO 8601, UTC). Omit it to publish immediately on push.
With it, the post stays queued until that time — a workflow also runs hourly
(`schedule: cron "5 * * * *"`) so scheduled posts go out automatically even if
nothing new was pushed that day.

## Posting cadence
Fixed posting days: **Monday + Thursday**. Claude queues each post with a
`publish_at` set to 9am Brisbane time (UTC+10, e.g. 23:00 UTC the day before) on
the next of those two days, so posts go out on schedule regardless of when the
graphic/caption was actually prepared and pushed.

At the start of each month, Claude generates ~8 post content briefs (topic mix +
suburb rotation) covering the month's Mon/Thu slots. The user turns each brief into
a graphic (via his own GPT session with the brand data), sends it back, and Claude
writes the caption and queues it for the correct date.
