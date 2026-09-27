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
  "targets": ["facebook", "instagram"]
}
```
