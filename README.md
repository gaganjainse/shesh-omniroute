# shesh-omniroute — Shesh wrapper around the OmniRoute gateway

Self-hosted, OpenAI-compatible LLM gateway for the whole Shesh stack. Runs our
fork ([`gaganjainse/OmniRoute`](https://github.com/gaganjainse/OmniRoute),
branch `release/v3.8.50`, upstream [`diegosouzapw/OmniRoute`](https://github.com/diegosouzapw/OmniRoute))
in a **rootless podman** container (docker works too) and exposes
`http://localhost:20128/v1` to every Shesh client:

- desktop apps and agents use it as the single model endpoint
- the swarm LLM worker routes through it when `SHESH_OMNIROUTE_BASE_URL` is set
  (see `shesh-ecosystem/tools/llm_adapter.py`, provider `omniroute`)

Everything here is real and tested: CLI lifecycle (start/stop/status/logs),
config rendering, health-wait, secrets handoff via `shesh-secrets`.

## Quick start

```bash
pipx install .
shesh-omniroute start            # pulls image, starts container, waits for health
shesh-omniroute status           # endpoint + health + routing-ready check
export SHESH_OMNIROUTE_BASE_URL=http://localhost:20128/v1
```

Gateway API key: generated on first start, stored with 0600 at
`~/.config/shesh/omniroute/api.key`, or pushed into shesh-secrets as
`omniroute:api-key` when shesh-secrets is installed.

## Layout

- `src/shesh_omniroute/` — the whole wrapper (stdlib only)
- `templates/` — container env + routes config rendered on start
- `tests/` — full offline test suite (mocked container backend + health server)
- `Containerfile` — builds the gateway image from our fork

## Security

Security posture and vulnerability reporting: [canonical ecosystem security
policy](https://github.com/gaganjainse/shesh-ecosystem/blob/main/SECURITY.md).
