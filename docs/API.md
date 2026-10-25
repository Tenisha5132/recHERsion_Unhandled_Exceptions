# HTTP API

The app exposes HTML pages plus a small JSON API for the chat client and deployment checks.

## `GET /healthz`
Returns a non-sensitive health snapshot. Responses include `Cache-Control: no-store`.

```json
{
  "status": "ok",
  "app": "recHERsion",
  "version": "1.0.0",
  "retrieval": {"backend": "bm25", "chunks": 12},
  "database": {"status": "ok"},
  "llm": {"configured": false, "mode": "rules"}
}
```

If the SQLite journal is unavailable, `status` becomes `degraded`, `database.status` becomes `unavailable`, and the endpoint returns HTTP 503.

## `POST /api/chat`
Request:

```json
{"message": "I have a cold"}
```

Limits: the message is trimmed and must be between 1 and 2000 characters. Invalid JSON, a missing message, or an empty message returns HTTP 400. A message above the limit returns HTTP 413. Request bodies above `MAX_REQUEST_BYTES` (64 KB by default) also return HTTP 413. Requests use the anonymous cookie and do not require authentication.

The response always contains:

- `mood`: `theme`, `emoji`, optional `joke`
- `safety`: `action` and `message`
- `insight`: `flag_level`, `pattern`, `reasoning`, citations and doctor questions
- `remedy`: source-backed advice and citations
- `general`: `reply`, `mode`, `scope`
- `support`: care options, or `null` for off-topic messages
- `trace`: compact per-agent summaries

General and off-topic replies intentionally omit period retrieval, insight and remedy content. Women's-health messages use the retrieval and citation path. Urgent and distress messages override both.

## `GET /export.json`
Downloads the current anonymous session's saved entries as JSON. The response includes `app`, `version`, `exported_at`, and `entries`, and is sent with a `Content-Disposition: attachment` header. It never includes the display-name cookie or another session's entries.

## `GET /summary.pdf`
Downloads a de-identified clinician summary generated from the current anonymous session's saved entries.

## `GET /robots.txt`
Disallows crawling. All responses also include `X-Robots-Tag: noindex, nofollow`.

## Response headers
All HTTP responses include:

- `Content-Security-Policy`: same-origin scripts, styles, media and connections; no framing
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `Permissions-Policy: geolocation=(self), camera=(), microphone=()`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-Permitted-Cross-Domain-Policies: none`
- `X-Request-ID`: a generated or validated request identifier
- `X-Robots-Tag: noindex, nofollow`

Dynamic pages and API responses also send `Cache-Control: no-store`. Static assets and generated audio use their own cache policy.

Set `COOKIE_SECURE=true` when serving over HTTPS.

## Smoke check
```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```
