# forge-examples

Runnable examples and showcases for [FORGE](https://github.com/ncmlabs/forge),
an agent-native programming language. Core keeps only the minimal examples its
conformance suite and docs need (`basics`, `errors`, `llm`); the showcases live
here so people and agents can browse and copy them.

These folders were imported verbatim from `ncmlabs/forge` `examples/` at commit
`26b2219` and are validated by `validation.toml`.

## Pinned FORGE version

CI validates every example against the pinned FORGE release **v0.2.0**. The pin
lives in one place:

```yaml
# .github/workflows/validate.yml
env:
  FORGE_VERSION: v0.2.0
```

To bump it: change `FORGE_VERSION` to the new release tag and re-run the
validator locally against that binary (`FORGE=./forge python3 scripts/validate.py`).
Some showcases need `v0.2.x` (see the note below), so bumps are not automatic.

## Layout

| Folder | What it shows |
| --- | --- |
| `agents/` | Agent showcases and smoke tests: debate/fact-check pool/support/toolkit agents, Slack responder and adapter, inbound triager, approval gate, PR review bot, clone-dev walking skeleton, mastermind pattern, PR history miner, dev-cycle and wake-rehydration smokes. |
| `command/` | `command` and `exec` intrinsic acceptance examples: argv, env, workdir, timeouts, background+cancel, stderr, failures, plus exec and skill composition. |
| `observer/` | "Standalone runtime inspector that connects to any running FORGE server" — wardens, confidence, token economy, stuck detection, knowledge stores. |
| `sentinel/` | "AI-Powered Repo Health Dashboard" — FORGE monitoring FORGE, exercising exec, the skill bridge and `>>` composition. |
| `server/` | Smallest HTTP server: one `endpoint` backed by a task. |
| `session/` | Session intrinsics: status, hooks, isolate (git-worktree sandbox), placeholder lifecycle, verification contracts and contradiction detection, plus live Claude/Codex engine variants. |
| `skill_project/` | Project-level skill declarations in `forge.project.toml`. |
| `skills/` | Skill trees used by the examples (`slack`, `github`, `ollama`) plus a GitHub-skill demo driving `gh` CLI operations. |
| `tictactoe/` | Multi-agent tic-tac-toe game system (platform, room agent, AI opponent, matchmaking). |
| `wiki/` | A documentation wiki built entirely in FORGE: browse, confidence-gated search, LLM answers and generated reference docs. |

## Running an example

Grab a FORGE binary (or download the pinned release) and run from the repo root:

```bash
# type-check one file, or a whole multi-file project
forge check agents/debate.forge
forge check tictactoe/platform.forge tictactoe/room_agent.forge \
  tictactoe/ai_opponent.forge tictactoe/matchmaking.forge --merge

# execute with the mock provider — no API keys, no network
FORGE_MOCK=1 forge run command/command_success.forge

# execute a multi-file project through its manifest
FORGE_MOCK=1 forge run --manifest tictactoe/forge.project.toml
```

Validate the whole corpus the way CI does:

```bash
FORGE=./forge python3 scripts/validate.py
```

`scripts/validate.py` mirrors the core suite's `tests/example_validation_tests.rs`:
`check = "ok"` cases must produce no checker errors (warnings are reported but
tolerated), `run = "mock"` cases are executed with `FORGE_MOCK=1`, and
`run = "live_only"` cases are skipped because they need real providers,
credentials or external side effects.

## Web showcases stay on v0.2.x

`wiki/`, `sentinel/`, `observer/` and `server/` use the web app stack
(`endpoint`, `forge serve`, static assets) that is being removed from core in
[ncmlabs/forge#485](https://github.com/ncmlabs/forge/issues/485). They stay
pinned to the v0.2.x release line until they are ported to whatever replaces it;
the remaining folders can follow newer releases.

## Known limitations

The `slack`, `github` and `ollama` skill trees live in `skills/`, and the
manifests and configs that reference them were rewritten to resolve in this
layout. `forge check` has no `--manifest`/`--config` flag yet, so the pinned CLI
cannot register those capabilities — tracked as
[ncmlabs/forge#495](https://github.com/ncmlabs/forge/issues/495). The eight
affected cases (`agents/slack-responder`, `agents/inbound-triager`,
`agents/pr-review-bot`, `agents/slack-adapter`, `agents/clone-dev-skeleton`,
`agents/pr-history-miner`, `sentinel/`, `skill_project/`) carry
`pending = "ncmlabs/forge#495"` in `validation.toml`, are reported as `PENDING`
and are not counted as failures; drop the marker once the flag lands.
