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
  "llm": {"configured": false, "mode": "rules"}
}
```

## `POST /api/chat`
Request:

```json
{"message": "I have a cold"}
```

Limits: the message is trimmed and must be between 1 and 2000 characters. Invalid JSON, a missing message, or an empty message returns HTTP 400. A message above the limit returns HTTP 413. Requests use the anonymous cookie and do not require authentication.

The response always contains:

- `mood`: `theme`, `emoji`, optional `joke`
- `safety`: `action` and `message`
- `insight`: `flag_level`, `pattern`, `reasoning`, citations and doctor questions
- `remedy`: source-backed advice and citations
- `general`: `reply`, `mode`, `scope`
- `support`: care options, or `null` for off-topic messages
- `trace`: compact per-agent summaries

General and off-topic replies intentionally omit period retrieval, insight and remedy content. Women's-health messages use the retrieval and citation path. Urgent and distress messages override both.

## Response headers
All HTTP responses include:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(self), camera=(), microphone=()`
- `X-Request-ID`: a generated or validated request identifier

Set `COOKIE_SECURE=true` when serving over HTTPS.

## Smoke check
```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```
