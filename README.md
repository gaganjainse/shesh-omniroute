# 🌀 shesh-omniroute — Free Big Models Gateway for Shesh

> **Optional to local AI in final product** — local Ollama primary (phi4-mini, qwen2.5-coder:3b, moondream2, nomic-embed-text) 6GB VRAM offline, no API key. Where you enable OmniRoute cloud free fallback in finished product is your choice (settings GUI).

> **For making ecosystem (dev):** Use free big industry models via OmniRoute gateway — Claude/GPT/Gemini/DeepSeek/Llama/Mistral/Qwen/Kimi/GLM etc free, 291 providers, 90+ free, 500+ models, 1.53B free tokens/month.

This repo wraps forked `gaganjainse/OmniRoute` (from `diegosouzapw/OmniRoute` MIT, 38.9k★, 6k commits).

## What OmniRoute gives

- **291 providers, 90+ free, 500+ models** — Kimi, Claude (via Kiro free ~50 credits/mo), GPT (via Pollinations/Requesty/Puter free), Gemini 60M tokens/mo, DeepSeek V3.2/R1 free via SiliconFlow/NVIDIA NIM, Llama 3.1 8B/70B/3.3 70B via Groq 14.4k req/day free, Mistral Large 3 1B tokens/mo, Qwen3-Max, Kimi K2 1M context, GLM-4-Flash permanently free, etc.
- **1.53B free tokens/month documented** (up to 2.15B first month with signup credits) + permanently free no-cap providers (SiliconFlow, GLM-CN, Kilo, OpenCode Zen)
- **RTK + Caveman compression 15-95% tokens** (~89% avg) stretches free tiers
- **One endpoint** `http://localhost:20128/v1` OpenAI-compatible — any tool (Claude Code, Cursor, Cline) points there
- **19 routing strategies**, **105 MCP tools**, **A2A v0.3**, **Desktop/PWA**, **43 i18n locales**, **MIT self-hosted**

See full study: `../shesh-ecosystem/docs/OMNIROUTE_STUDY.md` or original `https://github.com/diegosouzapw/OmniRoute`

## Separation: product vs factory

- **shesh-ecosystem = product** — clean, manifest, locks, architecture docs, gates. Local Ollama primary. OmniRoute optional cloud fallback where you enable is your choice (settings GUI `SeshaConfig.qml`).
- **shesh-workspace = factory** — messy dev works: session protocol, swarm, secure PAT, efficiency, model-agnostic adapter, travel mode. Keeps ecosystem clean, new chats don't mix.
- **shesh-omniroute = gateway** — wraps OmniRoute fork, provides `omniroute_generate` MCP tool with same model-agnostic adapter (strict JSON schema, validation+repair loop 3 retries, fallback chain free-first→stub, LLM-as-judge score >=0.7), so quality consistent across free big models.

## How to use to MAKE ecosystem (free, no money)

**You are NOT running local models for work you are doing** — those models run in final Shesh system, not for making it. But including them in design helps future quality not decrease much.

For making ecosystem, use free big industry models via OmniRoute:

```bash
# 1. Install OmniRoute (free, no keys needed for basic free providers)
npm install -g omniroute
omniroute
# Dashboard http://localhost:20128, API http://localhost:20128/v1

# 2. Connect free providers (no signup for some)
# Dashboard → Providers → Kiro AI (free Claude ~50 credits/month) or OpenCode Free (no auth)

# 3. Point coding tool
ANTHROPIC_BASE_URL=http://localhost:20128 claude
OPENAI_BASE_URL=http://localhost:20128/v1 codex
# Cursor/Cline: Base URL http://localhost:20128/v1, Model auto

# 4. In Arena, set
export OPENAI_BASE_URL=http://localhost:20128/v1
export OPENAI_API_KEY=any  # OmniRoute key from dashboard
# Model auto or kimi-k2, claude-sonnet-4.5, gpt-4o-mini, gemini-2.5-flash — OmniRoute picks cheapest free that works, auto-fallback Tier1 Sub → Tier2 API → Tier3 Cheap → Tier4 Free
```

## How it becomes optional to local AI in final product

Final Shesh on MSI Sword 16 HX:

```python
# shesh-mind router
if cloud.enabled and policy.allows(not protected path):
    # Optional cloud fallback — user choice in settings GUI
    model = omniroute_router.pick(role="planner", free_only=True)  # free big models via OmniRoute
else:
    model = local_router.pick(role="planner")  # phi4-mini, qwen2.5-coder:3b local 6GB
```

Where you enable is your choice — via `~/.config/shesh/config.toml` or GUI `SeshaConfig.qml` → Cloud toggle.

Policy `SKILLS_POLICY.md`: protected paths (.ssh, Vaults/, Job) never sent to cloud regardless.

## Free, no money

All 90+ free tiers documented in OmniRoute dashboard `/dashboard/free-tiers`:
- Qoder AI Qwen3-Max, Kimi-K2 unlimited free
- Pollinations GPT, Llama, Claude no key
- Cloudflare AI 50+ models 10k neurons/day free
- NVIDIA NIM GLM, MiniMax ~40 RPM free
- Cerebras GLM, Kilo Code Auto free, OpenCode Zen 6 rotating free coding models, etc.

1.53B tokens/mo + compression 15-95% → never hit limits.

## Integration with model-agnostic workflow

`manifests/models.toml` now has 15 free models with capabilities, prio.
`tools/llm_adapter.py` 5-layer guard: strict JSON schema, uniform prompt, validation+repair loop 3 retries, fallback chain free-first→stub, LLM-as-judge score >=0.7.
`tools/model_router.py` capability-based routing.

Run:
```bash
python tools/model_router.py --role planner --list
python tools/llm_adapter.py --role planner --goal "organize Downloads" --prompt "organize"
python scripts/eval_model_agnostic.py --role planner --tasks 2 --free-only
```

Quality consistent across free big models, small local does not decrease quality much because schema+validation+grading same.

## Fork

Forked from https://github.com/diegosouzapw/OmniRoute → https://github.com/gaganjainse/OmniRoute
This wrapper `shesh-omniroute` adds Shesh-specific MCP tool and settings integration.

License: MIT (same as OmniRoute)
