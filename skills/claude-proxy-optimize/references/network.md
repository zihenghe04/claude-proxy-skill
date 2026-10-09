# Platform discovery and references / 平台发现与参考

## Discovery / 发现

Use the installed client's own configuration-directory entry and the running core's arguments as the source of truth. Common Clash Verge Rev roots are beneath macOS `~/Library/Application Support/`, Windows `%APPDATA%`, and Linux `$XDG_CONFIG_HOME` or `~/.config`. Application IDs, service runtime roots, sockets and schemas vary between versions. Search filenames first; inspect only the relevant files. Do not copy paths from somebody else's machine.

以已安装客户端的“配置目录”和运行内核参数为准。macOS 通常位于用户 Library/Application Support，Windows 在 APPDATA，Linux 在 XDG_CONFIG_HOME 或 .config。应用 ID、服务运行目录、套接字、配置结构会变；先搜文件名，再读相关字段，不套用别人的路径。

Mihomo commonly exposes `GET /configs`, `GET /rules`, `GET /proxies`, `GET /connections`, and `GET`/`PUT /proxies/{URL-encoded-group}`. Check the current official API before mutations. Connection metadata is private browsing data: filter locally to the domain under investigation and do not publish raw responses. Use loopback HTTP or an existing Unix socket; never enable a public controller for convenience.

Mihomo 常见 API 为 configs/rules/proxies/connections 以及代理组 GET/PUT。修改前核对当前官方接口。连接元数据是私有浏览信息，只在本地筛选正在调查的域名。控制器使用回环地址或已有 Unix 套接字，不为方便而开放公网。

OS network checks: macOS `networksetup -getinfo <discovered-service>` and `scutil --proxy`; Windows network adapter/route/DNS settings; Linux `ip addr`, `ip route` and `resolvectl` where installed. Absence of a command is not proof of absent networking. Do not change OS DNS/IPv6 as an automatic first step.

系统检查应适配 OS：macOS 使用已发现的服务名和 networksetup/scutil；Windows 检查网卡、路由、DNS；Linux 在可用时使用 ip/resolvectl。命令缺失不代表无网络。不要默认先改系统 DNS/IPv6。

## Verification matrix / 验证矩阵

| Surface / 项目 | Evidence / 证据 |
|---|---|
| Claude routing / 分流 | Live matched rule + chain, web and API trace / 实际命中规则、连接链、网页/API 出口 |
| DNS transport / 传输 | Upstream 443 connection through selected group / 上游 443 连接走指定组 |
| DNS disclosure / 暴露 | Baseline vs deep browser leak test / 浏览器深度检测前后对比 |
| Ordinary browsing / 日常访问 | User browser, overseas + direct + intranet as relevant / 用户浏览器验证海外、直连及所需内网 |
| Persistence / 持久化 | Re-activation and live selection / 重载后运行配置和节点选择 |
| IP reputation / 信誉 | Optional third-party score, protocol and hosting type separately / 可选第三方评分，另看协议和机房属性 |

NTP carries time, not the client's timezone. Sending NTP through a proxy does not change browser/OS timezone. Do not treat unofficial IP scores as ban probabilities. HTTP 200 from a trace does not test account eligibility.

NTP 传输时间，不传输客户端时区；代理 NTP 不会改变浏览器/系统时区。第三方 IP 分数不是封号概率，trace 的 HTTP 200 也不证明账号资格。

## Sources / 来源

Recheck current sources when implementing; this project summarizes a workflow, not an official Anthropic policy.

- [Mihomo DNS configuration](https://wiki.metacubex.one/config/dns/): policy, direct and proxy bootstrap DNS, explicit proxy suffixes.
- [Mihomo API](https://wiki.metacubex.one/api/): current controller behavior.
- [Clash Verge extensions](https://www.clashverge.dev/guide/extend.html): profile extensions and DNS overwrite precedence.
- [Clash Verge scripts](https://www.clashverge.dev/guide/script.html): supported persistent customization.
- [Claude Code network configuration](https://code.claude.com/docs/en/network-config): official network requirements.
- [Claude Code authentication](https://code.claude.com/docs/en/authentication): login credentials are not established ban markers.
- [Net.Coffee domain-routing guide](https://ip.net.coffee/claude/site.html): a third-party domain reference; shared services are optional, broad keyword/NTP claims are not adopted.
- [Net.Coffee DNS test](https://ip.net.coffee/dns/): optional browser acceptance test.

Domain entries are operational candidates, not a guarantee of a complete or permanent Anthropic allowlist. Update from observed traffic and official docs. IP/ASN-wide rules need current ownership verification and are omitted from the default plan.

域名列表是候选分流清单，不保证完整或永久有效。根据实际流量与官方文档更新；IP/ASN 全段规则需核实当前归属，默认方案不加入。
