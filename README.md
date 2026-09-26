# Council

A private research dashboard for three AI investment analysts: business quality, valuation, and risk. The mandate is US-listed common stocks, a 3–5 year horizon, and moderate risk.

## Use

Start with **Discover candidates** for a focused search across sectors, or **Compare symbols** for 1–8 tickers. The council gathers independent research, then each analyst reviews the others and submits revised views. The shortlist preserves dissent and allows insufficient evidence. It never places trades.

All roles currently use `gpt-6-astra`. Separate roles are not independent model diversity. A unanimous vote is not a calibrated probability or proof of investment quality. Discovery is not an exhaustive market screen.

## Project contents

- `app/`: dashboard, authenticated research endpoint, and connection status endpoint.
- `lib/council.ts`: three analysts, research tools, debate sequence, and rate-limit handling.
- `lib/council-types.ts`: stock validation and deterministic shortlist rules.
- `components/`, `build/`, `scripts/`: interface primitives and build/runtime support.
- `package-lock.json`: reproducible dependency versions.

## Local setup

Requires Node 22.13+ and npm.

```sh
npm ci
cp .env.example .env.local
npm run dev
```

Configure the key in `.env.local` before running research. The local preview uses the starter’s local sign-in flow. A server-side `OPENAI_API_KEY` is required in the ignored `.env.local`; optional `OPENAI_MODEL` overrides the default. Never expose the key in browser code or commit it. API usage is billed separately by OpenAI.

For a production build, run `npm run build`. The server output is Cloudflare Worker compatible. Sites owns production authentication and private audience controls. Set `OPENAI_API_KEY` as a Sites secret before deploying; a local env file does not configure the hosted site.

## Decision rules

A research candidate requires three supportive verdicts, source links from the actual search citations, a positive USD quote with a supporting cited URL and a date within seven days, and no material risk objection. Missing evidence blocks a candidate classification. A risk veto produces Pass. Valuation ranges are AI estimates with assumptions, not forecasts.

The evidence comes from web research, not a licensed real-time price feed. Dates, accounting periods, source reliability, valuation assumptions, and model conclusions require human review. Views are saved only in page memory and disappear when refreshed or replaced by a new session.

## Verification and current blockers

- TypeScript checks and production build passed.
- Symbol normalization, invalid-input rejection, agreement, stale-evidence handling, missing quote sources, and risk veto checked.
- Browser tabs and WebMCP staging/readback checked, including invalid input without changing the selected symbols.
- API authentication and model availability verified.
- After credits were added, a complete live MSFT research/debate test passed: three research reports, three revised ballots, cited sources, and a combined verdict.
- Requests were reduced and research runs sequentially to fit the account’s token limits. Rate-limit errors wait before bounded retries; billing and other errors are not retried.
- The dashboard is privately published. The temporary publishing credential was explicitly authorized. Hosted API-secret setup remains incomplete; a proposed transfer exposing private key material was rejected and was not executed. The working API key remains in the local ignored env file.

## GitHub and hosting

GitHub stores this project’s source. The app requires a server runtime and cannot run its AI backend on static GitHub Pages. The existing private Sites deployment remains separate. Its server-side API secret still needs configuration; publishing the code to GitHub does not transfer that secret.

Environment files, credentials, generated builds, dependencies, and scratch files are excluded. `.env.example` contains names only, never a key. Preserve the bundled third-party license files.
