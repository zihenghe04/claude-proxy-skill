---
name: claude-proxy-optimize
description: Diagnose and optimize Claude routing, proxy exit selection, and DNS privacy in Clash Verge Rev or Mihomo, preserving normal web and intranet access. Use for Claude proxy issues, IPv6 exits, DNS leaks, or comparing nodes; not for account bans or credential cleanup. 支持中文操作。
---

# Claude proxy optimization

Respond in the user's language. For Chinese instructions read [references/workflow.zh-CN.md](references/workflow.zh-CN.md); for platform details and sources read [references/network.md](references/network.md). The English workflow below is authoritative and equivalent to the Chinese reference.

## Discover and establish a baseline

Discover the OS, installed client, active subscription, generated configuration, running core, controller endpoint, local HTTP proxy port, system proxy, TUN, DNS hijack, and browser secure-DNS behavior. Do not assume ports, service names, paths, node countries, or subscriptions. Compare saved settings with the live controller. A GUI's DNS switch does not prove queries use the tunnel. A user-level socket listing may miss a privileged core.

Keep diagnostics local. Never print or upload subscription URLs, passwords, UUID credentials, controller secrets, cookies, API keys, full configuration, or raw connection history. `scripts/proxy_tool.py inspect --config <active.yaml>` prints only an allowlisted summary; use `--show-names` only locally when candidate names are necessary. Do not dump config with grep patterns that can also match `uuid` or tokens.

Test Claude web and API routes, an ordinary overseas site, an ordinary local/direct site, and any user-reported failures before changing settings. Record exact browser errors and inspect failing subresources, not just the homepage status. Test DNS and WebRTC separately. Browser-generated certificate warnings must not be bypassed.

## Decide what to change

- Disabling Wi-Fi IPv6 or setting Mihomo `ipv6: false` cannot force a remote proxy server to use IPv4. Compare actual Claude trace exits; `curl -4` to a local HTTP proxy only constrains the local connection.
- Add a manual Claude-specific group using existing nodes. Fixing Claude must not change the general proxy group. Prefer a stable, reachable, appropriate-region exit; evaluate IPv4/IPv6 separately from IP reputation. A node label is not a verified exit location.
- Start with explicit suffix rules for the core Claude domains. Enable shared telemetry/support rules only when the user needs those surfaces and understands that suffix rules also affect unrelated applications using those services. Avoid global `sentry`, `sift`, or `datadog` keyword rules and global NTP redirection.
- Keep DNS policy scoped to Claude by default. For demonstrated general DNS leakage, separately route ordinary proxied DNS through encrypted upstreams while keeping direct/local-site DNS on a suitable direct encrypted resolver. Preserve local split DNS, VPN, `.local`, `.lan`, reverse lookup, fake-IP exceptions, and existing tunnel rules. Do not globally substitute overseas DNS just to make a leak test green.
- Explicit `https://<resolver-IP>/dns-query#<group>` avoids plaintext DNS and forces that DNS connection through the selected group. Verify syntax against current Mihomo documentation. Configure separate `proxy-server-nameserver` bootstrap resolution for proxy node hostnames so the tunnel does not depend on resolving itself through itself. Use independent IP-literal encrypted bootstrap resolvers or preserve a proven existing bootstrap. Do not expose the controller publicly or disable TLS verification.

## Plan and apply within authorization

When the user requests diagnosis, stay read-only. When they request optimization, perform the necessary reversible changes without inventing another approval gate; obey actual host permissions. Never expand the task to credential/device-ID cleanup, account cycling, timezone spoofing, or server-side changes.

Use a private local backup outside Git before editing. Capture the active profile ID, affected extension/DNS files, selected groups, and rollback instructions. Backups contain secrets: restrict access and do not upload them. Use `scripts/proxy_tool.py plan --config <active.yaml> --node <existing-node> --output <local-untracked-directory>` to generate reviewable group, rule and DNS-policy overlays. It does not apply them. `--include-support` adds shared services. An existing group name is rejected; choose another name or safely update the existing group manually.

Merge generated entries into the active subscription's existing extension files; preserve unrelated `prepend`, `append`, `delete`, DNS policies and groups. In Clash Verge, global/per-profile DNS overwrite may supersede extension DNS: update the actual effective layer. Do not edit generated runtime YAML as the sole persistent change. Re-activate/reload the subscription through the supported client path and validate with its installed Mihomo binary if available (`mihomo -t -f <candidate>`). A backup or candidate file may include real credentials; never commit it.

For authorized node comparison, use a manual test group:

```text
python proxy_tool.py probe --socket <discovered-core-socket> --proxy http://127.0.0.1:<port> --group <manual-group> --nodes <node-a> <node-b>
```

On platforms without Unix sockets use `--controller http://127.0.0.1:<controller-port>`. Supply API auth only via `MIHOMO_API_SECRET`, not a command argument or tracked file. The helper temporarily switches that group and restores/verifies its selection in `finally`; do not run concurrent probe jobs. A crash, kill, or core shutdown can still interrupt restoration: record the original choice and verify it afterward. Testing disrupts new requests in that group briefly; do not modify the user's general group to compare nodes. No per-node proxy endpoint? Create a temporary isolated group through supported extensions, then remove only your own test changes after verification.

Risk queries are optional and external: `--risk` sends each measured public exit IP to Net.Coffee; explain the destination before using it and honor user authorization. `--show-ips` prints exit IPs locally. Default output uses numbered candidates and per-run salted exit IDs, never node names or full IPs. A third-party score is not Anthropic's internal score; IPv6 results can be incomplete. One trace timing is not a speed/RTT benchmark. The helper restores the original node; separately persist any final selection through the client UI/profile cache.

## Verify and report

After applying, verify all of the following, then stop routine testing:

1. Live rules point Claude web/API, authentication and requested supporting domains at the dedicated group; unrelated sites keep their intended routes.
2. Trace requests to `https://claude.ai/cdn-cgi/trace` and `https://api.anthropic.com/cdn-cgi/trace` show the selected exit. They verify routing, not login or model access. Do not issue paid API requests without authorization.
3. Actual encrypted DNS upstream connections follow the intended groups; direct-site DNS and local/intranet sites remain usable.
4. Browser deep DNS test improves relative to baseline; normal overseas and local websites, reported failures, and required login/CDN resources visibly load in the user's actual browser.
5. Re-activation preserves changes and selected groups. Confirm persistence from effective config and live API, not just an editor's save toast.

If normal browsing regresses, repair or roll back the specific DNS/routing change immediately, preserving other user changes. Do not declare success just because a leak test passes. Distinguish temporary core/node outages from a proved configuration defect. Report changes, selected node, live acceptance, unresolved limits and private rollback location. No account-safety guarantees; no claim that deleting local identifiers erases server records.
