# Security policy

## Reporting a vulnerability
Please do not open a public issue for a security problem. Use GitHub's private vulnerability reporting for this repository, or contact the maintainer through the repository profile. Include the affected route, reproduction steps, and the impact you observed.

## Scope
In scope:
- Authentication or session-cookie weaknesses
- Unauthorized access to another anonymous journal
- Injection, path traversal, or unsafe file access
- Exposure of API keys, environment variables, or local trace data
- Cross-site scripting or unsafe HTML rendering
- Denial-of-service issues in the chat or sound routes

Out of scope:
- Missing medical features or differences in clinical guidance
- Reports that require a compromised device or browser extension
- Issues in third-party services such as Google Maps or an LLM provider

## Data handling
recHERsion stores anonymous journal entries in SQLite and keeps an anonymous ID in an HTTP-only cookie. Distress and general/off-topic messages are not saved. Do not deploy a shared instance with `.env`, `data/app.db`, or `data/agent_trace.jsonl` committed or publicly served.

## Deployment checklist
- Set `COOKIE_SECURE=true` behind HTTPS.
- Set a model key only through the host environment or an uncommitted `.env`.
- Keep `data/` on a private persistent volume.
- Do not expose the debug trace file publicly.
- Run `python scripts/smoke_test.py --base-url https://your-host` after deployment.
- Review the privacy page and trace retention before inviting users.
