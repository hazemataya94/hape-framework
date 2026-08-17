# LinkedIn Automation

## Purpose

Export posts from a **public** LinkedIn profile URL into local files.

This integration is **best-effort** and **unauthenticated**.

LinkedIn often serves an auth wall or empty guest page to automated clients.

LinkedIn's User Agreement restricts automated collection; use this only for profiles you are authorized to export, and prefer LinkedIn's official data export when you need a complete archive of your own content.

## Prepare browser HTML export (recommended first)

When a live fetch hits an auth wall, run prepare first.

It prints save-as-HTML instructions, then opens LinkedIn login in your default browser.

HAPE does not collect passwords, cookies, or API tokens.

```
hape linkedin posts prepare \
  --profile-url https://www.linkedin.com/in/<slug>/ \
  --output-dir /path/to/output
```

Print instructions only (do not open a browser):

```
hape linkedin posts prepare \
  --profile-url https://www.linkedin.com/in/<slug>/ \
  --output-dir /path/to/output \
  --no-open
```

After login:

1. Open Recent activity for that profile.
2. Scroll until the posts you want are visible.
3. Save the page as HTML (Chrome/Edge/Firefox: Save Page As → HTML).
4. Run download with `--html-file`.

## Download public posts

```
hape linkedin posts download \
  --profile-url https://www.linkedin.com/in/<slug>/ \
  --output-dir /path/to/output \
  --format both \
  --max-posts 50
```

Outputs:

- `posts.json` when `--format` is `json` or `both`
- `posts.md` when `--format` is `markdown` or `both`

## Parse a saved public HTML page

If a live fetch hits an auth wall, save the profile or recent-activity HTML from a normal browser session and parse it locally:

```
hape linkedin posts download \
  --profile-url https://www.linkedin.com/in/<slug>/ \
  --output-dir /path/to/output \
  --html-file /path/to/saved-page.html \
  --format both
```

## Rules

- `--profile-url` must be a public `/in/<slug>` URL.
- No LinkedIn login, cookies, or API tokens are accepted by this client.
- Live fetches are rate-limited and may fail with `LINKEDIN_PUBLIC_VIEW_UNAVAILABLE`.
- On auth wall, run `hape linkedin posts prepare` and retry download with `--html-file`.
