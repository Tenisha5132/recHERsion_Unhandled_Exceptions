# recHERsion demo video script

Target length: **6:30**. Hard stop: **7:00**.

This script is written for a screen recording with voiceover. Use only synthetic examples. Do not show real health data, `.env`, API keys, `data/app.db`, or `data/agent_trace.jsonl`.

## Before recording

1. Use a fresh incognito window so there is no old journal data.
2. Open the deployed app or run `make run` and use `http://127.0.0.1:8000`.
3. Set browser zoom to 110% and hide bookmarks or unrelated tabs.
4. Open these tabs in advance:
   - Home / Talk
   - Journal
   - Sound library
   - Support
   - Privacy
   - `GET /healthz`
   - README or a screenshot of the multi-agent workflow diagram
   - A terminal showing `make check` output, if you want a quality shot
5. Test audio once on the sound page, then stop playback before recording.
6. Confirm the microphone level and do a 10-second test recording.
7. Keep the demo messages ready to paste so there is no typing delay.
8. Do not press “Delete my data” during the main demo. If you show the confirmation dialog, cancel it.

## Demo messages

Use these exact examples:

1. `My periods are 50 days apart and I have been tired for two months.`
2. `I have a cold and a sore throat.`
3. `I am soaking a pad every hour and feel faint.` (safety demo only)
4. Optional, if time allows: `What is the capital of France?`

Expected results:

- Example 1: cycle pattern worth discussing, NHS citations, doctor questions, gynaecology support, and 8 agent steps.
- Example 2: general-health guidance, GP/pharmacy support, no period citations, no remedy citations, and 6 agent steps.
- Example 3: urgent override with emergency guidance. This is not a normal saved check-in.
- Example 4: off-topic scope reply with no support cards.

## 0:00–0:25 — Opening

**Show:** The Talk page, with the recHERsion heading and chat input visible.

**Say:**

“Hi, I’m [your name], and this is recHERsion: a private, multi-agent health support app for women’s health.

It is designed for screening and awareness, not diagnosis. It helps someone describe symptoms in their own words, notice patterns, check cited sources, keep a private journal, and find real support.”

## 0:25–0:55 — The problem

**Show:** The home page, then briefly the workflow diagram or README architecture section.

**Say:**

“Women’s health symptoms are often dismissed, normalized, or diagnosed late. People may wait months while trying to remember what changed and what to ask a clinician.

recHERsion brings four things into one place: a symptom conversation, source-grounded insights, a journal a person can take to an appointment, and practical support options.

It is not trying to replace a doctor. It is trying to make the next conversation better.”

## 0:55–1:25 — How the agents work

**Show:** The multi-agent workflow diagram.

**Say:**

“At a high level, the router first decides whether this is a women’s-health message, a general-health message, an off-topic message, or a safety concern.

Safety checks run first and last. For women’s-health messages, the app extracts structured details such as cycle length and symptoms, then retrieves the most relevant knowledge-base chunks. Only those chunks can support the insight and self-care response.

General-health and off-topic messages deliberately skip period retrieval. They receive a scoped reply instead, so a cold does not turn into endometriosis advice.”

## 1:25–2:35 — Core demo: cycle pattern

**Show:** Talk page.

**Do:** Paste and send:

`My periods are 50 days apart and I have been tired for two months.`

**Say while the response loads:**

“The router classifies this as women’s health. The first safety pass has already ruled out red flags and distress. Extraction is pulling out the cycle gap and the tiredness. Retrieval is selecting the most relevant chunks, and the insight agent is checking them against the rules.”

**Show:** The response card, citations, questions to ask a doctor, and support card.

**Say:**

“The result is a pattern worth discussing with a doctor, not a diagnosis. It explains that a cycle gap above 35 days is outside the typical 21-to-35-day range and links to the NHS source it used.

The questions are there to make the appointment more useful. The support card offers nearby gynaecology, general-doctor, and hospital options.”

**Do:** Expand “How this was answered.”

**Say:**

“This is the full trace: router, safety, extraction, retrieval, insight, remedy, mood, and final safety. Eight agents, with the source path visible instead of a hidden black box.”

## 2:35–3:05 — Scope fix: a cold is not a period problem

**Show:** Talk page.

**Do:** Send:

`I have a cold and a sore throat.`

**Say:**

“This was an important bug fix. Earlier, an unrelated message could pull period content simply because retrieval always returned the top chunks.

Now the router sends this to the general-health path. It skips period retrieval, insight, and self-care citations. The reply stays cautious, and the support card points to a GP or pharmacy.”

**Show:** The response and its six-step trace.

**Say:**

“No period sources appear. No unrelated remedy appears. The app is allowed to say it does not have a sourced answer for a general symptom.”

## 3:05–3:30 — Safety override

**Show:** Talk page.

**Do:** Send:

`I am soaking a pad every hour and feel faint.`

**Say:**

“Safety still overrides everything. This message triggers the urgent path before normal extraction or retrieval. It tells the person to seek emergency care and does not treat this as a routine journal entry.

The same pattern applies to distress language: supportive guidance comes first, and the normal screening flow is skipped.”

**Show:** The urgent response and then return to the chat. Do not dwell on the example.

## 3:30–4:15 — Journal and clinician summary

**Show:** Journal page.

**Say:**

“The cycle check-in was saved to a local journal under an anonymous ID. The cold message and the urgent safety message were not saved in the normal journal flow.

The journal gives the user a simple timeline, a de-identified clinician summary in PDF form, and a delete control.”

**Do:** Click “Download doctor summary.” Show the PDF briefly.

**Say:**

“The PDF is de-identified and includes the saved timeline plus suggested discussion points. It is not a medical record, and the dataset can be deleted by the user.”

## 4:15–4:55 — Sound library

**Show:** Sound library.

**Do:** Play a short clip such as “Calm tide” or “Night rain,” adjust volume, and set the sleep timer to 15 minutes.

**Say:**

“The sound page includes fifteen locally generated ambient profiles for calm, focus, breathing, sleep, and grounding.

There is volume control, looping, and a sleep timer. Users can also add their own music, which stays in their browser using local storage and is never uploaded to the server.

Audio is a comfort tool, not treatment.”

## 4:55–5:25 — Support and privacy

**Show:** Support page.

**Say:**

“The support page includes emergency numbers, Tele-MANAS, findahelpline, and nearby-care map searches. Location is requested only when the user presses the button, and it stays in the browser.”

**Show:** Privacy page.

**Say:**

“The privacy page explains what is stored: anonymous entries in SQLite, an HTTP-only anonymous cookie, optional name-only login, and local agent traces. If a model key is configured, de-identified text may go to an OpenAI-compatible provider. Without a key, the app uses rule-based fallbacks.”

## 5:25–6:05 — Engineering quality and deployment

**Show:** Terminal with `make check` finishing, or the GitHub Actions page. Then show `/healthz` in the browser.

**Say:**

“The project is built to be inspectable and deployable. The test suite now has ninety-four tests covering routing, irrelevant-retrieval filtering, safety, support, cookies, database access, validation, security headers, and page contracts.

GitHub Actions runs the suite on Python 3.11 and 3.12. The health endpoint reports the retrieval backend, chunk count, version, and whether a model is configured, without exposing secrets.

Docker files, a production start command, a smoke-test script, and deployment documentation are included. The LLM or SLM path is optional; the app still works with rules when no model is configured.”

## 6:05–6:30 — Closing

**Show:** Return to the Talk page.

**Say:**

“recHERsion is a screening and awareness tool, not a diagnosis. Its job is to help someone describe what is happening, see a cited pattern clearly, ask better questions, and find support sooner.

The code, tests, architecture diagrams, and demo script are all in the repository. Thank you for watching.”

## Optional cuts and fallback lines

If the demo is running long, cut in this order:

1. The PDF viewer shot.
2. The off-topic example.
3. The sleep-timer interaction.
4. The GitHub Actions shot.

If the model is not configured, say: “This instance is using the rule-based fallback, which is the default and the safety-critical path.”

If a response is slow, do not fill with “um.” Continue the architecture narration or say: “While that runs, the trace is the audit view for what each agent did.”

If the network is unavailable, use a local instance and say: “This is running locally, with the same app and knowledge base.”

## Do not show

- API keys or `.env` contents
- `data/app.db` or raw trace files
- Real names, phone numbers, locations, or health histories
- The delete confirmation actually deleting demo data
- A claim that the app diagnoses or prescribes
- A promise that the LLM path is active when no key is configured
