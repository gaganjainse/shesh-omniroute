# shesh-omniroute

> **Shesh wrapper around the OmniRoute gateway.** Self-hosted, OpenAI-compatible
> LLM gateway for the whole Shesh stack — runs the OmniRoute fork in a rootless
> podman container and exposes `http://localhost:20128/v1` to every client.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python) ![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue) ![CI](https://github.com/gaganjainse/shesh-omniroute/actions/workflows/ci.yml/badge.svg)

- **License:** GPL-3.0-or-later
- **Owner:** Gagan Jain ([@gaganjainse](https://github.com/gaganjainse))
- **Layer:** Soma (gateway — optional cloud fallback)
- **Part of:** [shesh-ecosystem](https://github.com/gaganjainse/shesh-ecosystem)

---

## Quick start

```bash
pipx install .
shesh-omniroute start            # pulls image, starts container, waits for health
shesh-omniroute status           # endpoint + health + routing-ready check
export SHESH_OMNIROUTE_BASE_URL=http://localhost:20128/v1
```
Gateway API key: generated on first start, stored with `0600` at
`~/.config/shesh/omniroute/api.key`, or pushed into shesh-secrets as
`omniroute:api-key` when shesh-secrets is installed.

## Layout

- `src/shesh_omniroute/` — the whole wrapper (stdlib only)
- `templates/` — container env + routes config rendered on start
- `tests/` — full offline test suite (mocked container backend + health server)
- `Containerfile` — builds the gateway image from the fork

## Status

Component CI is green (reusable ecosystem pipeline). Security posture and
vulnerability reporting: [SECURITY.md](SECURITY.md).

## Documentation index

- **Part of:** [shesh-ecosystem](https://github.com/gaganjainse/shesh-ecosystem)
- **Compiled reading:** [shesh-docs](https://github.com/gaganjainse/shesh-docs)

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
