# Claude Proxy Skill

[English](README.md) · [简体中文](README.zh-CN.md)

An installable AI skill for diagnosing and improving Claude routing and DNS privacy with **Clash Verge Rev / Mihomo**. It discovers your environment, proposes scoped changes, backs up locally, and verifies Claude **and ordinary browsing** afterward.

No subscription, account, node, exit IP, private configuration, or diagnostic history from the original machine is included. The workflow targets macOS, Windows and Linux; the observed desktop workflow was on macOS, and other OS integrations require local discovery and validation. It does not promise account safety or remove authentication/device identifiers.

## Install

Requires Git and Python 3.10+. Windows users can use `py` instead of `python3`.

```sh
git clone https://github.com/zihenghe04/claude-proxy-skill.git
cd claude-proxy-skill
python3 install.py --target codex
```

For Claude Code:

```sh
python3 install.py --target claude
```

For other agents supporting `~/.agents/skills`:

```sh
python3 install.py --target agents
```

An alternative skill root can be passed with `--dest /path/to/skills`. Existing installations are never overwritten. Installation copies only the skill and does not alter proxy settings. Restart or refresh your AI client after installing. A UI-only or remote/cloud AI session without access to your computer cannot operate your local proxy.

## Ask your AI

Codex:

```text
Use $claude-proxy-optimize to inspect my Clash configuration, optimize Claude routing and DNS privacy, and verify that my usual websites still work. Back up before changing anything.
```

Claude Code:

```text
/claude-proxy-optimize Inspect my proxy, compare suitable Claude exits, and apply the verified configuration without disrupting normal browsing.
```

[Claude Code supports personal skill folders and slash invocation](https://code.claude.com/docs/en/skills). The core skill uses standard SKILL.md frontmatter; agents/openai.yaml provides optional Codex UI metadata. Other agents must support local skills and provide filesystem/shell or desktop-control tools; this project does not grant permissions or install a proxy client.

## Included tools

The AI can follow the skill without Python automation. Helpers require `curl` for live probes and PyYAML for YAML inspection/planning. Install dependencies inside a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows use `.venv\Scripts\python.exe`. The following paths are relative to this repository; after installation, scripts live inside the installed skill folder.

```sh
.venv/bin/python skills/claude-proxy-optimize/scripts/proxy_tool.py inspect --config /path/to/active.yaml
.venv/bin/python skills/claude-proxy-optimize/scripts/proxy_tool.py plan --config /path/to/active.yaml --node EXISTING_NODE --output runs/plan-01
```

Inspection uses an output allowlist; add `--show-names` only for local candidate selection. Planning emits three permission-restricted local overlays and never edits the active configuration. The AI merges them into the appropriate persistent client layer, preserves existing entries and independent proxy-bootstrap DNS, then reloads and verifies.

```sh
.venv/bin/python skills/claude-proxy-optimize/scripts/proxy_tool.py probe --controller http://127.0.0.1:9090 --proxy http://127.0.0.1:7890 --group Claude --nodes NODE_A NODE_B
```

Ports and names above are examples, not defaults to impose on your machine. For an existing Unix socket use `--socket /path/to/core.sock` instead of `--controller`. Pass controller secrets only through `MIHOMO_API_SECRET` in your local environment. Probe temporarily switches the specified manual group, restores and verifies the original choice, and prints numbered candidates with per-run salted exit IDs. Do not run concurrent probes; verify restoration after forced interruption. Select and persist your final node separately in the client.

`--include-support` adds shared monitoring/CDN/customer-service domains to a generated plan; those rules can also affect other applications. It is opt-in. `--risk` sends measured public exit IPs to Net.Coffee, an optional third-party service; it is off by default. `--show-ips` reveals exit addresses only in local output. IP scores are neither Anthropic scores nor ban probabilities.

## What this workflow learned

- Local IPv6 settings do not force a remote node's outbound protocol. Measure the Claude exit itself.
- DNS hijack/fake-IP and encrypted DNS are separate from DNS following a proxy.
- A green DNS leak test can coexist with broken local websites. Preserve direct/split DNS and test everyday sites in the user's browser.
- Keep Claude on its own manual group; do not repeatedly change the general group or blindly redirect shared telemetry and NTP.
- Save in profile extensions/DNS overwrite, verify the live core, and re-activate to check persistence.

The [third-party domain guide](https://ip.net.coffee/claude/site.html) informed the domain candidates; the workflow checks [Mihomo DNS documentation](https://wiki.metacubex.one/config/dns/) and [Clash Verge extension behavior](https://www.clashverge.dev/guide/extend.html) before applying. It deliberately does not adopt the claim that NTP reveals client timezone, and does not automate credential or device-ID deletion.

## Privacy and validation

No analytics, auto-upload, subscription import, or background service. Network probes make explicitly requested trace requests; optional risk/browser tests contact third parties. Backups, generated overlays and reports stay outside version control. Never submit a real subscription, credential, full configuration, connection history, private IP, or screenshot in an issue. Public repository ownership is naturally visible on GitHub.

```sh
python3 -m unittest discover -s tests -v
python3 tools/privacy_check.py
```

Tests cover sensitive-field exclusion, scoped overlay generation, interrupted-probe restoration and non-destructive installation. The privacy check is a guardrail, not a substitute for reviewing staged files. No tests contact live nodes or paid APIs. See [CONTRIBUTING.md](CONTRIBUTING.md) for anonymized bug reports.

License: [MIT](LICENSE). Unaffiliated with Anthropic, Clash Verge, MetaCubeX or Net.Coffee.
