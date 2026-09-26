# Council — Three investment minds

An AI research dashboard that brings three perspectives to US stocks: **business quality, valuation, and risk**. Built for a **3–5 year investing horizon** and a **moderate-risk mandate**.

Council gathers research, lets its analysts challenge one another, and presents a combined view with sources and visible disagreements. It does not place trades.

## Meet the council

| Analyst | Focus |
| --- | --- |
| The Fundamentalist | Competitive advantages, cash generation, business durability, and growth |
| The Valuer | Price assumptions, valuation scenarios, and margin of safety |
| The Skeptic | Balance-sheet resilience, downside scenarios, and reasons the thesis could fail |

The three roles use the same underlying model by default. Different prompts do not create independent model diversity, and agreement is not proof that a conclusion is correct.

## Use the dashboard

1. Choose **Discover candidates** for a focused search across US sectors, or **Compare symbols** to enter 1–8 comma-separated symbols, such as `MSFT, V, BRK.B`.
2. Click **Convene council**. Research uses your OpenAI API account and incurs API charges.
3. Watch the reports and discussion in **Council room**.
4. Review **Shortlist** for each stock's combined view, supporting arguments, risks, and what would change the analysts' minds.
5. Open **Sources** and check the original evidence before acting.

Discovery searches for a small set of candidates; it does not screen the entire US market. Results stay in the current page only. Refreshing or starting another session replaces them.

## Run locally

### Requirements

- Node.js 22.13 or later and npm.
- An OpenAI API key with available credits and access to the configured model and web search.
- A local development environment capable of running the included Cloudflare/Vinext tooling.

### Install

```sh
git clone https://github.com/aqalaf/investment-council.git
cd investment-council
npm ci
cp .env.example .env.local
```

Open `.env.local` in your local editor and set `OPENAI_API_KEY` to your own key. Keep that file private; it is ignored by Git. The optional `OPENAI_MODEL` setting defaults to `gpt-6-astra`. Any replacement model must support the research tools and structured outputs used by this app.

Then start the dashboard:

```sh
npm run dev
```

Open **http://localhost:5173**. If the app requests sign-in, use the starter's local sign-in flow at **http://localhost:5173/signin-with-chatgpt**. Local development uses a mock identity; it is not production authentication.

### Check and build

```sh
npx tsc --noEmit
npm run build
```

The build generates a Cloudflare Worker-compatible server. This application needs a backend and cannot run its AI features on static GitHub Pages.

## Deploy with ChatGPT Sites

The source repository and hosted runtime are separate. Cloning or publishing this repository does not copy credentials or grant access to the existing deployment.

1. Create your own Site using the Sites workflow. The existing `.openai/hosting.json` links the original deployment; when deploying your own copy, have the workflow replace that linkage with your own Site's project ID. Do not reuse the original project's ID.
2. Open [ChatGPT Sites](https://chatgpt.com/sites), find your Site, and select **More actions → Settings**.
3. Add `OPENAI_API_KEY` as a **secret** environment variable. Optionally configure `OPENAI_MODEL`.
4. Save the settings and deploy a saved version to apply the new environment configuration.
5. Test one symbol before starting broader research.

See the [official Sites documentation](https://learn.chatgpt.com/docs/sites) for hosting and environment settings.

A local `.env.local` does not configure hosted secrets. Never put a key in `.openai/hosting.json`, client code, an issue, or a commit.

Production authentication relies on trusted identity headers supplied by Sites. If adapting the app to another hosting provider, implement and verify authentication there before exposing the research endpoint. Do not trust user-supplied identity headers.

## How decisions work

Research runs sequentially to reduce bursts of API usage. Each analyst produces an initial report, then reviews the shared research and earlier debate responses before submitting a revised view.

A stock qualifies for further research only when it has:

- Three supportive analyst verdicts.
- Supporting source citations.
- A positive USD price with a cited source and a date within seven days.
- No material objection from the risk analyst.

Missing evidence prevents a favorable classification. A material risk objection produces **Pass**. Fair-value ranges, when available, are scenario estimates rather than price forecasts.

## Troubleshooting

| Message or symptom | What to check |
| --- | --- |
| AI connection is not configured | Set the server-side key. For Sites, save the secret and redeploy. |
| AI key was rejected | Check or replace the key in the runtime's secret settings. |
| No available API credits | Check the API project's billing and available credits. |
| Rate limit reached | Wait before retrying; the app already performs bounded retries for temporary rate limits. |
| Model unavailable | Confirm the API project can access the configured model. |
| Sign-in required | Complete the appropriate local or hosted sign-in flow. |
| Session stopped or timed out | Start a smaller comparison. Partial reports are not a completed council result. |

## Project map

| Path | Purpose |
| --- | --- |
| `app/page.tsx` | Dashboard and session UI |
| `app/api/council/route.ts` | Authenticated research endpoint and streamed events |
| `app/api/health/route.ts` | Sign-in and key-presence checks |
| `app/chatgpt-auth.ts` | Sites identity integration |
| `lib/council.ts` | Analyst prompts, web research, debate, and retry handling |
| `lib/council-types.ts` | Input validation and combined decision rules |
| `components/ui/` | UI components |
| `build/`, `scripts/` | Development and hosting support |

Built with React, TypeScript, Vinext, Cloudflare Workers, and the OpenAI Agents SDK.

## Limitations and responsible use

This is a research aid, not personalized financial advice or an automated trading system. It does not assess your full financial circumstances.

Web research is not a licensed real-time market feed. Prices may be delayed, sources may be incomplete, and AI-generated facts, calculations, and interpretations can be wrong. Verify dates, financial statements, assumptions, and citations independently. “Moderate risk” is a research instruction, not a guarantee against losses.

The repository contains source code, not access to the maintainer's API account or hosted workspace. Anyone running a copy must provide their own credentials. Preserve the bundled third-party license notices.
